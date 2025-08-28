"""
Script d'initialisation de la base de données avec types UUID cohérents
Usage: python init_db.py
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def enable_uuid_extension():
    """Active l'extension UUID-OSSP dans PostgreSQL"""
    try:
        from sqlalchemy import create_engine, text
        
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_pass@localhost:5432/cleaning_db")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Activer l'extension UUID-OSSP
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.commit()
            print("Extension UUID-OSSP activee")
        
        return engine
        
    except Exception as e:
        print(f"ERREUR - Erreur activation UUID: {e}")
        return None

def create_tables():
    """Crée toutes les tables avec les modèles corrigés"""
    try:
        print("Connexion a la base de donnees...")
        
        # Activer l'extension UUID d'abord
        engine = enable_uuid_extension()
        if not engine:
            return False
        
        from sqlalchemy import text
        
        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_row = result.fetchone()
            print(f"SUCCESS - Connexion reussie: {test_row}")
        
        print("Import des modeles avec types UUID coherents...")
        
        # Import de la base
        from api.models.base import Base
        
        # Import de tous les modèles
        from api.models.user import User
        from api.models.performer import Performer  
        from api.models.room import Room
        from api.models.task import TaskTemplate, AssignedTask
        from api.models.session import CleaningSession, CleaningLog
        from api.models.export import Export
        
        print("SUCCESS - Tous les modeles importes")
        
        print("Creation des tables...")
        Base.metadata.create_all(bind=engine)
        print("SUCCESS - Tables creees avec succes")
        
        # Vérifier les tables créées
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            if tables:
                print(f"Tables creees: {', '.join(tables)}")
            else:
                print("WARNING - Aucune table trouvee")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Erreur lors de la creation des tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """Crée des données d'exemple"""
    try:
        print("Creation de donnees d'exemple...")
        
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from api.models.user import User, UserRole
        from api.models.performer import Performer
        from api.models.room import Room
        from api.models.task import TaskTemplate, TaskType
        
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_pass@localhost:5432/cleaning_db")
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Vérifier si des données existent déjà
            user_count = db.query(User).count()
            if user_count > 0:
                print(f"INFO - {user_count} utilisateur(s) deja present(s)")
                return True
            
            # Créer un utilisateur test
            test_user = User(
                firebase_uid="test-uid-123",
                full_name="Test Manager",
                role=UserRole.GERANTE
            )
            db.add(test_user)
            db.flush()  # Pour obtenir l'ID
            
            # Créer quelques performers
            performers_data = [
                "Marie Dupont",
                "Jean Martin", 
                "Sophie Leroux"
            ]
            
            for name in performers_data:
                performer = Performer(
                    name=name,
                    created_by_id=test_user.id
                )
                db.add(performer)
            
            # Créer quelques pièces
            rooms_data = [
                ("Salle de jeu", "Espace principal d'activité", 1),
                ("Cuisine", "Préparation des repas", 2),
                ("Salle de bain", "Sanitaires et change", 3),
                ("Entrée", "Hall d'accueil", 4)
            ]
            
            for name, desc, order in rooms_data:
                room = Room(
                    name=name,
                    description=desc,
                    display_order=order
                )
                db.add(room)
            
            # Créer quelques modèles de tâches
            tasks_data = [
                ("Désinfecter les surfaces", "Nettoyer et désinfecter toutes les surfaces"),
                ("Aspirer/Balayer", "Nettoyage des sols"),
                ("Vider les poubelles", "Évacuer les déchets"),
                ("Nettoyer les vitres", "Nettoyage des fenêtres et miroirs")
            ]
            
            for title, desc in tasks_data:
                task = TaskTemplate(
                    title=title,
                    description=desc,
                    type=TaskType.DAILY
                )
                db.add(task)
            
            db.commit()
            print("SUCCESS - Donnees d'exemple creees")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"WARNING - Erreur creation donnees d'exemple: {e}")
            return True  # Pas critique
        finally:
            db.close()
            
    except Exception as e:
        print(f"WARNING - Erreur donnees d'exemple: {e}")
        return True  # Pas critique

def main():
    """Fonction principale d'initialisation"""
    print("Initialisation de la base de donnees avec UUID...")
    
    # Créer les répertoires
    try:
        for directory in ["uploads", "logs"]:
            Path(directory).mkdir(exist_ok=True)
        print("Repertoires crees")
    except Exception as e:
        print(f"WARNING - Impossible de creer les repertoires: {e}")
    
    # Créer les tables
    if not create_tables():
        print("ERREUR - Echec de la creation des tables")
        sys.exit(1)
    
    # Créer des données d'exemple
    create_sample_data()
    
    print("SUCCESS - Initialisation terminee!")
    print("Services disponibles:")
    print("1. API: http://localhost:8000")
    print("2. Documentation: http://localhost:8000/docs") 
    print("3. Interface DB: http://localhost:8080")

if __name__ == "__main__":
    main()