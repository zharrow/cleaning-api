# diagnostic_unicode.py
#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes d'encodage Unicode
"""
import os
import sys
import locale
from pathlib import Path

def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

def check_encoding():
    """Vérifier l'encodage du système"""
    print_separator("ENCODAGE SYSTÈME")
    
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Répertoire courant: {os.getcwd()}")
    print(f"🔤 Encodage par défaut: {sys.getdefaultencoding()}")
    print(f"📝 Encodage filesystem: {sys.getfilesystemencoding()}")
    print(f"⌨️ Encodage stdin: {sys.stdin.encoding}")
    print(f"📺 Encodage stdout: {sys.stdout.encoding}")
    
    # Locale système
    try:
        loc = locale.getdefaultlocale()
        print(f"🌍 Locale système: {loc}")
    except:
        print("❌ Impossible de récupérer la locale")
    
    # Variables d'environnement importantes
    env_vars = ['PYTHONIOENCODING', 'LANG', 'LC_ALL', 'PYTHONPATH']
    print(f"\n📋 Variables d'environnement:")
    for var in env_vars:
        value = os.environ.get(var, "Non définie")
        print(f"   {var}: {value}")

def check_path_encoding():
    """Vérifier l'encodage du chemin"""
    print_separator("ANALYSE DU CHEMIN")
    
    current_path = Path.cwd()
    print(f"📁 Chemin complet: {current_path}")
    
    # Tester l'encodage de chaque partie du chemin
    parts = current_path.parts
    print(f"\n🔍 Analyse des parties du chemin:")
    
    for i, part in enumerate(parts):
        try:
            # Tester l'encodage UTF-8
            part_bytes = part.encode('utf-8')
            part_decoded = part_bytes.decode('utf-8')
            status = "✅"
        except UnicodeError as e:
            status = f"❌ {e}"
        
        print(f"   {i}: '{part}' → {status}")
        
        # Détecter les caractères problématiques
        for char in part:
            if ord(char) > 127:  # Caractères non-ASCII
                print(f"      ⚠️ Caractère non-ASCII détecté: '{char}' (code: {ord(char)})")

def check_database_config():
    """Vérifier la configuration de la base de données"""
    print_separator("CONFIGURATION BASE DE DONNÉES")
    
    # Chercher le fichier .env
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Fichier .env trouvé")
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Chercher DATABASE_URL
            for line in content.split('\n'):
                if line.startswith('DATABASE_URL'):
                    print(f"🔗 {line}")
                    
                    # Vérifier si client_encoding est défini
                    if 'client_encoding' in line:
                        print("✅ client_encoding défini")
                    else:
                        print("⚠️ client_encoding manquant")
                        print("   Ajoutez ?client_encoding=utf8 à la fin de l'URL")
                    
        except UnicodeDecodeError as e:
            print(f"❌ Erreur lecture .env: {e}")
            print("   Le fichier .env contient des caractères non-UTF8")
    else:
        print("❌ Fichier .env introuvable")

def test_database_connection():
    """Tester la connexion à la base de données"""
    print_separator("TEST CONNEXION BASE")
    
    try:
        # Tenter d'importer les modules
        import psycopg2
        print("✅ psycopg2 importé")
        
        # Lire la configuration
        from dotenv import load_dotenv
        load_dotenv()
        
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            print(f"🔗 URL base: {db_url[:50]}...")
            
            # Ajouter client_encoding si manquant
            if 'client_encoding' not in db_url:
                separator = "&" if "?" in db_url else "?"
                db_url_fixed = f"{db_url}{separator}client_encoding=utf8"
                print(f"🔧 URL corrigée: {db_url_fixed[:50]}...")
            else:
                db_url_fixed = db_url
            
            # Tester la connexion
            try:
                conn = psycopg2.connect(db_url_fixed)
                print("✅ Connexion PostgreSQL réussie")
                conn.close()
            except Exception as e:
                print(f"❌ Erreur connexion: {e}")
        else:
            print("❌ DATABASE_URL non trouvée dans .env")
            
    except ImportError as e:
        print(f"❌ Module manquant: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def provide_solutions():
    """Proposer des solutions"""
    print_separator("SOLUTIONS RECOMMANDÉES")
    
    current_path = str(Path.cwd())
    
    if "Nettoyage" in current_path:
        print("🎯 PROBLÈME IDENTIFIÉ: Caractères accentués dans le chemin")
        print("\n📋 Solutions (par ordre de préférence):")
        
        print("\n1️⃣ SOLUTION RAPIDE - Variables d'environnement:")
        print("   set PYTHONIOENCODING=utf-8")
        print("   set LANG=en_US.UTF-8")
        print("   alembic upgrade head")
        
        print("\n2️⃣ SOLUTION SCRIPT - Utiliser le script batch:")
        print("   run_alembic.bat upgrade")
        
        print("\n3️⃣ SOLUTION DÉFINITIVE - Renommer le dossier:")
        new_path = current_path.replace("Nettoyage", "Cleaning")
        print(f"   Renommer: {current_path}")
        print(f"   Vers:     {new_path}")
        
        print("\n4️⃣ SOLUTION .ENV - Forcer UTF-8 dans la chaîne de connexion:")
        print("   DATABASE_URL=postgresql://user:pass@host:port/db?client_encoding=utf8")
    
    else:
        print("🔍 Aucun caractère accentué détecté dans le chemin")
        print("Le problème peut venir de:")
        print("   - Configuration PostgreSQL")
        print("   - Variables d'environnement")
        print("   - Encodage du fichier .env")

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC D'ENCODAGE UNICODE")
    print("================================")
    
    check_encoding()
    check_path_encoding()
    check_database_config()
    test_database_connection()
    provide_solutions()
    
    print(f"\n✅ Diagnostic terminé")

if __name__ == "__main__":
    main()