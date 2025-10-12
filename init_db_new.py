"""
Script d'initialisation de la base de données avec système 3-tier
Crée des données d'exemple pour Developer/Admin/User + HACCP + Communication
Usage: python init_db_new.py
"""
import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

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
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.commit()
            print("✅ Extension UUID-OSSP activée")

        return engine

    except Exception as e:
        print(f"❌ Erreur activation UUID: {e}")
        return None

def create_tables():
    """Crée toutes les tables avec le système 3-tier"""
    try:
        print("🔌 Connexion à la base de données...")

        engine = enable_uuid_extension()
        if not engine:
            return False

        from sqlalchemy import text

        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_row = result.fetchone()
            print(f"✅ Connexion réussie")

        print("📦 Import des modèles...")

        # Import de la base
        from api.models.base import Base

        # Import système 3-tier
        from api.models.user import Developer, Admin, User, UserRooms
        from api.models.enterprise import Enterprise

        # Import modèles cLean
        from api.models.room import Room
        from api.models.task import TaskTemplate, AssignedTask
        from api.models.session import CleaningSession
        from api.models.cleaning_log import CleaningLog
        from api.models.export import Export

        # Import modèles HACCP
        from api.models.haccp_models import (
            Child, Supplier, Product, Batch, Meal, Temperature,
            Equipment, CleaningHaccp, NonCompliance, Document, MealChildren
        )

        # Import modèles Communication
        from api.models.communication_models import (
            Conversation, Message, Notification
        )

        print("✅ Tous les modèles importés")

        print("🏗️  Création des tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès")

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
                print(f"📋 Tables créées ({len(tables)}): {', '.join(tables)}")
            else:
                print("⚠️  Aucune table trouvée")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def seed_data():
    """Insère des données d'exemple avec système 3-tier"""
    try:
        print("\n🌱 Insertion des données d'exemple...")

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from api.models.user import Developer, Admin, User, UserRooms
        from api.models.enterprise import Enterprise
        from api.models.room import Room
        from api.models.task import TaskTemplate, AssignedTask
        from api.models.session import CleaningSession
        from api.models.haccp_models import Child, Supplier, Product, Meal
        from api.models.communication_models import Notification

        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_pass@localhost:5432/cleaning_db")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 1. Créer un Developer (Super Admin)
        developer = Developer(
            id=uuid.uuid4(),
            firebase_uid="dev_firebase_uid_123",
            email="developer@clean.com",
            full_name="Developer Admin",
            is_active=True
        )
        session.add(developer)
        print("✅ Developer créé")

        # 2. Créer une Enterprise
        enterprise = Enterprise(
            id=uuid.uuid4(),
            name="Micro-Crèche Les Petits Anges",
            address="123 Rue de la Paix, 75001 Paris",
            phone="01 23 45 67 89",
            email="contact@petitsanges.fr",
            siret="12345678901234",
            is_active=True
        )
        session.add(enterprise)
        session.flush()  # Pour obtenir l'ID
        print(f"✅ Enterprise créée: {enterprise.name}")

        # 3. Créer un Admin (Gestionnaire de la crèche)
        admin = Admin(
            id=uuid.uuid4(),
            firebase_uid="admin_firebase_uid_456",
            email="admin@petitsanges.fr",
            full_name="Marie Dupont",
            enterprise_id=enterprise.id,
            is_active=True
        )
        session.add(admin)
        print(f"✅ Admin créé: {admin.full_name}")

        # 4. Créer des Rooms
        rooms = [
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Salle de jeux", description="Espace de jeux principal", order=1),
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Salle de repos", description="Dortoir pour la sieste", order=2),
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Cuisine", description="Cuisine et préparation repas", order=3),
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Salle de bain", description="Sanitaires enfants", order=4),
        ]
        for room in rooms:
            session.add(room)
        print(f"✅ {len(rooms)} Rooms créées")

        # 5. Créer des Users (Employés avec PIN)
        users = [
            User(id=uuid.uuid4(), enterprise_id=enterprise.id, first_name="Sophie", last_name="Martin",
                 pin_code="1234", email="sophie.martin@petitsanges.fr", is_active=True),
            User(id=uuid.uuid4(), enterprise_id=enterprise.id, first_name="Julie", last_name="Bernard",
                 pin_code="5678", email="julie.bernard@petitsanges.fr", is_active=True),
            User(id=uuid.uuid4(), enterprise_id=enterprise.id, first_name="Claire", last_name="Petit",
                 pin_code="9012", email="claire.petit@petitsanges.fr", is_active=True),
        ]
        for user in users:
            session.add(user)
        session.flush()
        print(f"✅ {len(users)} Users créés")

        # 6. Assigner les Users aux Rooms (Many-to-Many)
        for user in users:
            for room in rooms[:3]:  # Chaque user a accès aux 3 premières pièces
                user_room = UserRooms(user_id=user.id, room_id=room.id)
                session.add(user_room)
        print("✅ Associations User-Room créées")

        # 7. Créer des TaskTemplates
        templates = [
            TaskTemplate(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Désinfecter les surfaces",
                        description="Surfaces de contact", category="Nettoyage", estimated_duration=15),
            TaskTemplate(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Passer l'aspirateur",
                        description="Sol et tapis", category="Nettoyage", estimated_duration=10),
            TaskTemplate(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Vider les poubelles",
                        description="Poubelles de la pièce", category="Nettoyage", estimated_duration=5),
        ]
        for template in templates:
            session.add(template)
        session.flush()
        print(f"✅ {len(templates)} TaskTemplates créés")

        # 8. Créer des AssignedTasks
        for room in rooms[:2]:  # Salle de jeux et Repos
            for template in templates:
                assigned = AssignedTask(
                    id=uuid.uuid4(),
                    enterprise_id=enterprise.id,
                    room_id=room.id,
                    task_template_id=template.id,
                    default_user_id=users[0].id,
                    frequency="daily",
                    is_active=True
                )
                session.add(assigned)
        print("✅ AssignedTasks créées")

        # 9. Créer une Session du jour
        today_session = CleaningSession(
            id=uuid.uuid4(),
            enterprise_id=enterprise.id,
            date=date.today(),
            status="in_progress"
        )
        session.add(today_session)
        print("✅ CleaningSession du jour créée")

        # 10. Créer des données HACCP

        # Supplier
        supplier = Supplier(
            id=uuid.uuid4(),
            enterprise_id=enterprise.id,
            name="Bio Ferme du Val",
            contact_name="Jean Legrand",
            phone="02 34 56 78 90",
            email="contact@bioferme.fr",
            haccp_certified=True,
            validation_date=date.today()
        )
        session.add(supplier)
        session.flush()
        print("✅ Supplier HACCP créé")

        # Children
        children = [
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Durand", first_name="Emma",
                  birth_date=date(2022, 3, 15), section="Babies", allergies="Lactose", is_active=True),
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Moreau", first_name="Lucas",
                  birth_date=date(2021, 7, 22), section="Toddlers", is_active=True),
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Lefebvre", first_name="Chloé",
                  birth_date=date(2020, 11, 8), section="Preschoolers", allergies="Arachides", is_active=True),
        ]
        for child in children:
            session.add(child)
        print(f"✅ {len(children)} Children créés")

        # Product
        product = Product(
            id=uuid.uuid4(),
            enterprise_id=enterprise.id,
            supplier_id=supplier.id,
            name="Lait Bio",
            category="Produits laitiers",
            allergens="Lactose",
            stock_unit="litres",
            current_stock=10.0,
            expiry_date=date.today() + timedelta(days=7)
        )
        session.add(product)
        print("✅ Product créé")

        # Meal
        meal = Meal(
            id=uuid.uuid4(),
            enterprise_id=enterprise.id,
            supplier_id=supplier.id,
            responsible_id=users[0].id,
            date=date.today(),
            meal_type="Lunch",
            description="Purée de carottes et poulet"
        )
        session.add(meal)
        print("✅ Meal créé")

        # 11. Créer des Notifications
        notifications = [
            Notification(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                recipient_type="Admin",
                recipient_id=admin.id,
                title="Bienvenue !",
                content="Votre crèche a été configurée avec succès",
                type="System",
                priority="Info",
                status="Unread"
            ),
            Notification(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                recipient_type="Admin",
                recipient_id=admin.id,
                title="Produit périmé",
                content="Le lait expire dans 7 jours",
                type="HACCP",
                priority="Warning",
                status="Unread"
            )
        ]
        for notif in notifications:
            session.add(notif)
        print(f"✅ {len(notifications)} Notifications créées")

        # Commit toutes les données
        session.commit()
        print("\n✅ Toutes les données d'exemple insérées avec succès !")

        # Résumé
        print("\n📊 Résumé des données créées:")
        print(f"  • 1 Developer: {developer.email}")
        print(f"  • 1 Enterprise: {enterprise.name}")
        print(f"  • 1 Admin: {admin.full_name}")
        print(f"  • {len(users)} Users (employés)")
        print(f"  • {len(rooms)} Rooms")
        print(f"  • {len(templates)} TaskTemplates")
        print(f"  • 1 CleaningSession (aujourd'hui)")
        print(f"  • 1 Supplier HACCP")
        print(f"  • {len(children)} Children")
        print(f"  • 1 Product, 1 Meal")
        print(f"  • {len(notifications)} Notifications")

        session.close()
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'insertion des données: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        session.close()
        return False

if __name__ == "__main__":
    print("🚀 Initialisation de la base de données cLean (système 3-tier)")
    print("=" * 60)

    # Étape 1: Créer les tables
    if not create_tables():
        print("\n❌ Échec de la création des tables")
        sys.exit(1)

    # Étape 2: Insérer les données d'exemple
    if not seed_data():
        print("\n❌ Échec de l'insertion des données")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 Initialisation terminée avec succès !")
    print("\n🔐 Identifiants de test:")
    print("  Developer: developer@clean.com")
    print("  Admin: admin@petitsanges.fr")
    print("  User PIN: 1234 (Sophie), 5678 (Julie), 9012 (Claire)")
    print("\n💡 La base de données est prête à être utilisée !")
