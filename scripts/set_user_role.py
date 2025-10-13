"""
Script pour définir le rôle d'un utilisateur Firebase (developer ou admin)
Usage: python scripts/set_user_role.py <firebase_uid> <role>
Exemples:
  python scripts/set_user_role.py abc123def456 developer
  python scripts/set_user_role.py xyz789ghi012 admin
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import firebase_admin
from firebase_admin import credentials, auth
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.user import Developer, Admin
import uuid

def init_firebase():
    """Initialise Firebase Admin SDK"""
    cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase-credentials.json"))
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

def set_custom_claim(firebase_uid: str, role: str):
    """Définit le custom claim 'role' pour un utilisateur Firebase"""
    if role not in ['developer', 'admin']:
        print(f"❌ Rôle invalide: {role}. Utilisez 'developer' ou 'admin'")
        return False

    try:
        # Vérifier que l'utilisateur existe
        user = auth.get_user(firebase_uid)
        print(f"✅ Utilisateur trouvé: {user.email}")

        # Définir le custom claim
        auth.set_custom_user_claims(firebase_uid, {'role': role})
        print(f"✅ Rôle '{role}' défini pour {user.email}")

        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def create_user_in_database(firebase_uid: str, email: str, role: str, first_name: str = None, last_name: str = None):
    """Crée l'utilisateur dans la base de données PostgreSQL"""
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_pass@localhost:5432/cleaning_db")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        if role == 'developer':
            # Créer un Developer
            developer = Developer(
                id=uuid.uuid4(),
                firebase_uid=firebase_uid,
                email=email
            )
            session.add(developer)
            session.commit()
            print(f"✅ Developer créé dans la DB: {email}")

        elif role == 'admin':
            # Vérifier qu'il y a au moins un developer pour created_by_id
            first_dev = session.query(Developer).first()
            if not first_dev:
                print("❌ Erreur: Aucun Developer trouvé. Créez d'abord un Developer.")
                return False

            # Créer un Admin
            if not first_name or not last_name:
                print("⚠️  Warning: first_name et last_name non fournis, utilisation de valeurs par défaut")
                first_name = email.split('@')[0]
                last_name = "Admin"

            admin = Admin(
                id=uuid.uuid4(),
                firebase_uid=firebase_uid,
                email=email,
                first_name=first_name,
                last_name=last_name,
                created_by_id=first_dev.id
            )
            session.add(admin)
            session.commit()
            print(f"✅ Admin créé dans la DB: {email}")

        session.close()
        return True

    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        session.rollback()
        session.close()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/set_user_role.py <firebase_uid> <role> [first_name] [last_name]")
        print("Exemples:")
        print("  python scripts/set_user_role.py abc123 developer")
        print("  python scripts/set_user_role.py xyz789 admin Marie Dupont")
        sys.exit(1)

    firebase_uid = sys.argv[1]
    role = sys.argv[2].lower()
    first_name = sys.argv[3] if len(sys.argv) > 3 else None
    last_name = sys.argv[4] if len(sys.argv) > 4 else None

    print(f"🔧 Configuration du rôle '{role}' pour l'utilisateur {firebase_uid}")
    print("=" * 60)

    # Initialiser Firebase
    init_firebase()

    # Récupérer l'email de l'utilisateur
    try:
        user = auth.get_user(firebase_uid)
        email = user.email
    except Exception as e:
        print(f"❌ Utilisateur Firebase introuvable: {e}")
        sys.exit(1)

    # 1. Définir le custom claim dans Firebase
    if not set_custom_claim(firebase_uid, role):
        sys.exit(1)

    # 2. Créer l'utilisateur dans la base de données
    if not create_user_in_database(firebase_uid, email, role, first_name, last_name):
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Configuration terminée avec succès !")
    print(f"\n📋 Résumé:")
    print(f"  • Email: {email}")
    print(f"  • Firebase UID: {firebase_uid}")
    print(f"  • Rôle: {role}")
    print(f"  • Custom claim Firebase: ✅")
    print(f"  • Enregistrement DB: ✅")
    print("\n💡 L'utilisateur peut maintenant se connecter avec ce rôle")
