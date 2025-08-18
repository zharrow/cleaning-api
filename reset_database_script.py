# reset_database.py
#!/usr/bin/env python3
"""
Script de réinitialisation complète de la base de données
Supprime tout et recrée depuis le début
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import time

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'en_US.UTF-8'

def print_step(step, description):
    """Afficher une étape avec style"""
    print(f"\n{'='*5} ÉTAPE {step}: {description} {'='*5}")

def print_success(message):
    """Afficher un message de succès"""
    print(f"✅ {message}")

def print_error(message):
    """Afficher un message d'erreur"""
    print(f"❌ {message}")

def print_warning(message):
    """Afficher un avertissement"""
    print(f"⚠️ {message}")

def print_info(message):
    """Afficher une information"""
    print(f"ℹ️ {message}")

class DatabaseResetter:
    def __init__(self):
        load_dotenv()
        self.parse_database_url()
        
    def parse_database_url(self):
        """Parser l'URL de la base de données"""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL non trouvée dans .env")
        
        # Parser postgresql://username:password@localhost:5432/cleaning_db?client_encoding=utf8
        import re
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
        match = re.match(pattern, db_url)
        
        if not match:
            raise ValueError(f"Format DATABASE_URL invalide: {db_url}")
        
        self.db_user = match.group(1)
        self.db_password = match.group(2)
        self.db_host = match.group(3)
        self.db_port = int(match.group(4))
        self.db_name = match.group(5)
        
        print_info(f"Base de données cible: {self.db_name} sur {self.db_host}:{self.db_port}")

    def connect_postgres(self, database='postgres'):
        """Connexion à PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=database,
                client_encoding='utf8'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        except Exception as e:
            print_error(f"Impossible de se connecter à PostgreSQL: {e}")
            return None

    def drop_database(self):
        """Supprimer la base de données"""
        print_step(1, "SUPPRESSION DE LA BASE DE DONNÉES")
        
        conn = self.connect_postgres()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Terminer toutes les connexions à la base
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity 
                WHERE pg_stat_activity.datname = '{self.db_name}'
                AND pid <> pg_backend_pid()
            """)
            
            # Supprimer la base de données
            cursor.execute(f'DROP DATABASE IF EXISTS "{self.db_name}"')
            print_success(f"Base de données '{self.db_name}' supprimée")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print_error(f"Erreur lors de la suppression: {e}")
            return False

    def create_database(self):
        """Créer une nouvelle base de données"""
        print_step(2, "CRÉATION DE LA NOUVELLE BASE")
        
        conn = self.connect_postgres()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Créer la base avec encodage UTF-8
            cursor.execute(f"""
                CREATE DATABASE "{self.db_name}" 
                WITH ENCODING 'UTF8' 
                LC_COLLATE='C' 
                LC_CTYPE='C' 
                TEMPLATE=template0
            """)
            
            print_success(f"Base de données '{self.db_name}' créée avec encodage UTF-8")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print_error(f"Erreur lors de la création: {e}")
            return False

    def cleanup_alembic(self):
        """Nettoyer les fichiers Alembic"""
        print_step(3, "NETTOYAGE DES FICHIERS ALEMBIC")
        
        # Supprimer le dossier versions s'il existe
        versions_dir = Path("alembic/versions")
        if versions_dir.exists():
            shutil.rmtree(versions_dir)
            print_success("Dossier alembic/versions supprimé")
        
        # Recréer le dossier versions
        versions_dir.mkdir(parents=True, exist_ok=True)
        print_success("Dossier alembic/versions recréé")
        
        # Créer un fichier __init__.py vide
        init_file = versions_dir / "__init__.py"
        init_file.touch()
        
        return True

    def init_alembic(self):
        """Initialiser Alembic depuis le début"""
        print_step(4, "INITIALISATION D'ALEMBIC")
        
        try:
            # Configurer l'environnement pour Windows
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['LANG'] = 'en_US.UTF-8'
            
            # Créer la migration initiale
            print_info("Création de la migration initiale...")
            result = subprocess.run([
                sys.executable, "-m", "alembic", 
                "revision", "--autogenerate", 
                "-m", "Initial migration with fixed auth system"
            ], env=env, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print_success("Migration initiale créée")
                print_info(f"Sortie: {result.stdout}")
            else:
                print_error(f"Erreur création migration: {result.stderr}")
                return False
            
            # Appliquer la migration
            print_info("Application de la migration...")
            result = subprocess.run([
                sys.executable, "-m", "alembic", 
                "upgrade", "head"
            ], env=env, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print_success("Migration appliquée avec succès")
                print_info(f"Sortie: {result.stdout}")
                return True
            else:
                print_error(f"Erreur application migration: {result.stderr}")
                return False
                
        except Exception as e:
            print_error(f"Erreur Alembic: {e}")
            return False

    def verify_tables(self):
        """Vérifier que les tables ont été créées"""
        print_step(5, "VÉRIFICATION DES TABLES")
        
        conn = self.connect_postgres(self.db_name)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Lister les tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            print_info(f"Tables créées ({len(tables)}):")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Vérifier les tables importantes
            expected_tables = ['users', 'performers', 'alembic_version']
            table_names = [t[0] for t in tables]
            
            all_good = True
            for expected in expected_tables:
                if expected in table_names:
                    print_success(f"Table '{expected}' présente")
                else:
                    print_error(f"Table '{expected}' manquante")
                    all_good = False
            
            cursor.close()
            conn.close()
            return all_good
            
        except Exception as e:
            print_error(f"Erreur vérification: {e}")
            return False

    def create_test_data(self):
        """Créer des données de test (optionnel)"""
        print_step(6, "CRÉATION DE DONNÉES DE TEST (OPTIONNEL)")
        
        response = input("Voulez-vous créer des données de test ? (y/N): ")
        if response.lower() != 'y':
            print_info("Pas de données de test créées")
            return True
        
        conn = self.connect_postgres(self.db_name)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Créer un utilisateur de test
            test_user_id = "550e8400-e29b-41d4-a716-446655440000"
            cursor.execute("""
                INSERT INTO users (id, firebase_uid, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, (test_user_id, "test_firebase_uid", "Gérant Test", "gerante", True))
            
            print_success("Utilisateur de test créé")
            
            # Créer des employés de test
            performers = [
                ("Marie", "Dupont", "marie.dupont@example.com"),
                ("Jean", "Martin", "jean.martin@example.com"),
                ("Sophie", "Bernard", "sophie.bernard@example.com")
            ]
            
            for first_name, last_name, email in performers:
                cursor.execute("""
                    INSERT INTO performers (id, first_name, last_name, email, manager_id, is_active)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
                """, (first_name, last_name, email, test_user_id, True))
            
            print_success(f"{len(performers)} employés de test créés")
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print_error(f"Erreur création données test: {e}")
            return False

    def run_reset(self):
        """Exécuter la réinitialisation complète"""
        print("🔄 RÉINITIALISATION COMPLÈTE DE LA BASE DE DONNÉES")
        print("=" * 60)
        
        print_warning("Cette opération va SUPPRIMER toutes les données !")
        confirmation = input("Êtes-vous sûr de vouloir continuer ? (tapez 'RESET'): ")
        
        if confirmation != 'RESET':
            print_info("Opération annulée")
            return False
        
        success = True
        success &= self.drop_database()
        success &= self.create_database()
        success &= self.cleanup_alembic()
        success &= self.init_alembic()
        success &= self.verify_tables()
        success &= self.create_test_data()
        
        if success:
            print("\n🎉 RÉINITIALISATION TERMINÉE AVEC SUCCÈS !")
            print("=" * 50)
            print("✅ Base de données recréée")
            print("✅ Tables créées avec le nouveau système")
            print("✅ Alembic initialisé")
            print("✅ Système d'authentification corrigé")
            print("\n🚀 Vous pouvez maintenant démarrer l'API:")
            print("   python -m uvicorn main:app --reload --port 8000")
        else:
            print("\n❌ ÉCHEC DE LA RÉINITIALISATION")
            print("Vérifiez les erreurs ci-dessus et recommencez")
        
        return success

def main():
    """Fonction principale"""
    try:
        resetter = DatabaseResetter()
        resetter.run_reset()
    except Exception as e:
        print_error(f"Erreur fatale: {e}")
        return False

if __name__ == "__main__":
    main()