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
        from api.models.session import CleaningSession, SessionStatus
        from api.models.haccp_models import (
            Child, Supplier, Product, Batch, Meal, Temperature,
            Equipment, CleaningHaccp, NonCompliance, Document, MealChildren
        )
        from api.schemas.haccp_schemas import (
            Section, MealType, Checkpoint, CleaningFrequency,
            NonComplianceType, NonComplianceStatus, DocumentCategory
        )
        from api.models.communication_models import Notification

        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_pass@localhost:5432/cleaning_db")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 1. Créer un Developer (Super Admin)
        developer = Developer(
            id=uuid.uuid4(),
            firebase_uid="FUp76fogAFU7HUcGbvTbsOvUR4s1",
            email="developer@clean.com"
        )
        session.add(developer)
        session.flush()
        print("✅ Developer créé")

        # 2. Créer un Admin (Gestionnaire de la crèche) AVANT Enterprise
        admin = Admin(
            id=uuid.uuid4(),
            firebase_uid="PrV0dpj3mOYpvfTnWIciXtLiZcC2",
            email="admin@petitsanges.fr",
            first_name="Florent",
            last_name="Admin",
            created_by_id=developer.id  # Créé par le Developer
        )
        session.add(admin)
        session.flush()  # Pour obtenir l'ID
        print(f"✅ Admin créé: {admin.first_name} {admin.last_name}")

        # 3. Créer l'Enterprise (1:1 avec Admin)
        enterprise = Enterprise(
            id=uuid.uuid4(),
            admin_id=admin.id,
            name="Micro-Crèche Les Petits Anges",
            legal_form="SARL",
            siret="12345678901234"
        )
        session.add(enterprise)
        session.flush()  # Pour obtenir l'ID
        print(f"✅ Enterprise créée: {enterprise.name}")

        # 4. Créer des Rooms
        rooms = [
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Salle de jeux", description="Espace de jeux principal"),
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Salle de repos", description="Dortoir pour la sieste"),
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Cuisine", description="Cuisine et préparation repas"),
            Room(id=uuid.uuid4(), enterprise_id=enterprise.id, name="Salle de bain", description="Sanitaires enfants"),
        ]
        for room in rooms:
            session.add(room)
        print(f"✅ {len(rooms)} Rooms créées")

        # 5. Créer des Users (Employés avec PIN)
        users = [
            User(id=uuid.uuid4(), enterprise_id=enterprise.id, first_name="Sophie", last_name="Martin",
                 pin_code="1234", email="sophie.martin@petitsanges.fr", is_active=True, created_by_id=admin.id),
            User(id=uuid.uuid4(), enterprise_id=enterprise.id, first_name="Julie", last_name="Bernard",
                 pin_code="5678", email="julie.bernard@petitsanges.fr", is_active=True, created_by_id=admin.id),
            User(id=uuid.uuid4(), enterprise_id=enterprise.id, first_name="Claire", last_name="Petit",
                 pin_code="9012", email="claire.petit@petitsanges.fr", is_active=True, created_by_id=admin.id),
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
                    room_id=room.id,
                    task_template_id=template.id,
                    default_performer_id=users[0].id,  # Note: champ non renommé mais pointe vers user.id
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
            status=SessionStatus.EN_COURS
        )
        session.add(today_session)
        session.flush()
        print("✅ CleaningSession du jour créée")

        # 10. Créer des données HACCP enrichies

        # Suppliers (3 fournisseurs)
        suppliers = [
            Supplier(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Bio Ferme du Val",
                contact_name="Jean Legrand",
                phone="02 34 56 78 90",
                email="contact@bioferme.fr",
                address="12 Route de la Ferme, 75001 Paris",
                haccp_certified=True,
                validation_date=date.today() - timedelta(days=30)
            ),
            Supplier(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Fruits et Légumes Martin",
                contact_name="Sophie Martin",
                phone="02 34 56 78 91",
                email="contact@martin-fruits.fr",
                address="45 Avenue des Maraîchers, 75002 Paris",
                haccp_certified=True,
                validation_date=date.today() - timedelta(days=60)
            ),
            Supplier(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Boulangerie Artisanale",
                contact_name="Pierre Dubois",
                phone="02 34 56 78 92",
                email="pain@boulangerie.fr",
                haccp_certified=False,
                validation_date=None
            ),
        ]
        for supplier in suppliers:
            session.add(supplier)
        session.flush()
        print(f"✅ {len(suppliers)} Suppliers HACCP créés")

        # Children (5 enfants)
        children = [
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Durand", first_name="Emma",
                  birth_date=date(2022, 3, 15), section=Section.BABIES.value, allergies="Lactose", is_active=True),
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Moreau", first_name="Lucas",
                  birth_date=date(2021, 7, 22), section=Section.TODDLERS.value, is_active=True),
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Lefebvre", first_name="Chloé",
                  birth_date=date(2020, 11, 8), section=Section.PRESCHOOLERS.value, allergies="Arachides", is_active=True),
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Bernard", first_name="Tom",
                  birth_date=date(2022, 1, 20), section=Section.BABIES.value, specific_diet="Sans gluten", is_active=True),
            Child(id=uuid.uuid4(), enterprise_id=enterprise.id, last_name="Petit", first_name="Léa",
                  birth_date=date(2021, 5, 10), section=Section.TODDLERS.value, allergies="Oeufs", is_active=True),
        ]
        for child in children:
            session.add(child)
        session.flush()
        print(f"✅ {len(children)} Children créés")

        # Products (6 produits)
        products = [
            Product(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[0].id,
                name="Lait Bio",
                category="Produits laitiers",
                allergens="Lactose",
                stock_unit="litres",
                current_stock=10.0,
                expiry_date=date.today() + timedelta(days=7)
            ),
            Product(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[1].id,
                name="Carottes Bio",
                category="Légumes",
                allergens=None,
                stock_unit="kg",
                current_stock=5.0,
                expiry_date=date.today() + timedelta(days=5)
            ),
            Product(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[1].id,
                name="Pommes",
                category="Fruits",
                allergens=None,
                stock_unit="kg",
                current_stock=8.0,
                expiry_date=date.today() + timedelta(days=10)
            ),
            Product(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[2].id,
                name="Pain complet",
                category="Céréales",
                allergens="Gluten",
                stock_unit="unités",
                current_stock=15.0,
                expiry_date=date.today() + timedelta(days=2)
            ),
            Product(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[0].id,
                name="Yaourt nature",
                category="Produits laitiers",
                allergens="Lactose",
                stock_unit="pots",
                current_stock=20.0,
                expiry_date=date.today() + timedelta(days=14)
            ),
            Product(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[1].id,
                name="Poulet Bio",
                category="Viandes",
                allergens=None,
                stock_unit="kg",
                current_stock=3.0,
                expiry_date=date.today() + timedelta(days=3)
            ),
        ]
        for product in products:
            session.add(product)
        session.flush()
        print(f"✅ {len(products)} Products créés")

        # Batches (3 lots)
        batches = [
            Batch(
                id=uuid.uuid4(),
                product_id=products[0].id,
                batch_code="LOT-2025-001",
                reception_date=date.today() - timedelta(days=2),
                received_quantity=10.0,
                is_compliant=True
            ),
            Batch(
                id=uuid.uuid4(),
                product_id=products[3].id,
                batch_code="LOT-2025-002",
                reception_date=date.today(),
                received_quantity=15.0,
                is_compliant=True
            ),
            Batch(
                id=uuid.uuid4(),
                product_id=products[5].id,
                batch_code="LOT-2025-003",
                reception_date=date.today() - timedelta(days=1),
                received_quantity=3.0,
                is_compliant=True
            ),
        ]
        for batch in batches:
            session.add(batch)
        session.flush()
        print(f"✅ {len(batches)} Batches créés")

        # Meals (3 repas)
        meals = [
            Meal(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[0].id,
                responsible_id=users[0].id,
                date=date.today(),
                meal_type=MealType.LUNCH,
                description="Purée de carottes et poulet"
            ),
            Meal(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[1].id,
                responsible_id=users[1].id,
                date=date.today(),
                meal_type=MealType.SNACK,
                description="Compote de pommes"
            ),
            Meal(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                supplier_id=suppliers[2].id,
                responsible_id=users[0].id,
                date=date.today() - timedelta(days=1),
                meal_type=MealType.BREAKFAST,
                description="Pain complet avec beurre et confiture"
            ),
        ]
        for meal in meals:
            session.add(meal)
        session.flush()
        print(f"✅ {len(meals)} Meals créés")

        # Temperatures (4 contrôles de température)
        temperatures = [
            Temperature(
                id=uuid.uuid4(),
                meal_id=meals[0].id,
                checkpoint=Checkpoint.RECEPTION,
                temperature=4.5,
                responsible_id=users[0].id,
                control_date=datetime.now() - timedelta(hours=3),
                is_compliant=True
            ),
            Temperature(
                id=uuid.uuid4(),
                meal_id=meals[0].id,
                checkpoint=Checkpoint.HOLDING,
                temperature=65.0,
                responsible_id=users[0].id,
                control_date=datetime.now() - timedelta(hours=1),
                is_compliant=True
            ),
            Temperature(
                id=uuid.uuid4(),
                meal_id=meals[0].id,
                checkpoint=Checkpoint.SERVICE,
                temperature=63.0,
                responsible_id=users[1].id,
                control_date=datetime.now(),
                is_compliant=True
            ),
            Temperature(
                id=uuid.uuid4(),
                meal_id=meals[1].id,
                checkpoint=Checkpoint.STORAGE,
                temperature=5.0,
                responsible_id=users[1].id,
                control_date=datetime.now() - timedelta(hours=2),
                is_compliant=True
            ),
        ]
        for temp in temperatures:
            session.add(temp)
        print(f"✅ {len(temperatures)} Temperatures créées")

        # Equipment (3 équipements)
        equipments = [
            Equipment(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Réfrigérateur principal",
                type="Fridge",
                last_control_date=date.today() - timedelta(days=15),
                target_temperature=4.0,
                is_compliant=True
            ),
            Equipment(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Four micro-ondes",
                type="Microwave",
                last_control_date=date.today() - timedelta(days=20),
                is_compliant=True
            ),
            Equipment(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Lave-vaisselle",
                type="Dishwasher",
                last_control_date=date.today() - timedelta(days=5),
                is_compliant=True
            ),
        ]
        for equipment in equipments:
            session.add(equipment)
        print(f"✅ {len(equipments)} Equipments créés")

        # CleaningHaccp (2 nettoyages HACCP)
        cleanings = [
            CleaningHaccp(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                zone="Cuisine",
                frequency=CleaningFrequency.DAILY,
                cleaning_date=datetime.now() - timedelta(hours=6),
                product_used="Détergent alimentaire",
                responsible_id=users[0].id
            ),
            CleaningHaccp(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                zone="Réfrigérateurs",
                frequency=CleaningFrequency.WEEKLY,
                cleaning_date=datetime.now() - timedelta(days=3),
                product_used="Désinfectant HACCP",
                responsible_id=users[1].id
            ),
        ]
        for cleaning in cleanings:
            session.add(cleaning)
        print(f"✅ {len(cleanings)} CleaningHaccp créés")

        # NonCompliances (2 non-conformités)
        non_compliances = [
            NonCompliance(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                responsible_id=users[0].id,
                type=NonComplianceType.TEMPERATURE,
                description="Température du réfrigérateur trop élevée (8°C au lieu de 4°C)",
                report_date=datetime.now() - timedelta(days=2),
                corrective_action="Appel du technicien, ajustement du thermostat",
                status=NonComplianceStatus.CORRECTED
            ),
            NonCompliance(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                responsible_id=users[1].id,
                type=NonComplianceType.PRODUCT,
                description="Lot de yaourts périmés trouvés dans le frigo",
                report_date=datetime.now() - timedelta(days=1),
                corrective_action="Destruction des produits, vérification de tous les stocks",
                status=NonComplianceStatus.CLOSED
            ),
        ]
        for nc in non_compliances:
            session.add(nc)
        print(f"✅ {len(non_compliances)} NonCompliances créées")

        # Documents (2 documents)
        documents = [
            Document(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Plan de Maîtrise Sanitaire 2025",
                category=DocumentCategory.COMPLIANCE,
                file_path="/documents/pms-2025.pdf",
                responsible_id=users[0].id,
                creation_date=date.today() - timedelta(days=10)
            ),
            Document(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                name="Relevés de températures - Janvier 2025",
                category=DocumentCategory.TEMPERATURES,
                file_path="/documents/temps-jan-2025.xlsx",
                responsible_id=users[1].id,
                creation_date=date.today() - timedelta(days=5)
            ),
        ]
        for doc in documents:
            session.add(doc)
        print(f"✅ {len(documents)} Documents créés")

        # MealChildren (associations repas-enfants)
        meal_children = [
            MealChildren(meal_id=meals[0].id, child_id=children[0].id, portion="Normale"),
            MealChildren(meal_id=meals[0].id, child_id=children[1].id, portion="Normale"),
            MealChildren(meal_id=meals[0].id, child_id=children[2].id, portion="Petite"),
            MealChildren(meal_id=meals[1].id, child_id=children[0].id, portion="Normale"),
            MealChildren(meal_id=meals[1].id, child_id=children[3].id, portion="Grande"),
            MealChildren(meal_id=meals[2].id, child_id=children[1].id, portion="Normale"),
            MealChildren(meal_id=meals[2].id, child_id=children[4].id, portion="Normale"),
        ]
        for mc in meal_children:
            session.add(mc)
        print(f"✅ {len(meal_children)} MealChildren associations créées")

        # 11. Notifications skipped (Enum issue to fix later)

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
        print(f"\n🏥 HACCP Module:")
        print(f"  • {len(suppliers)} Suppliers")
        print(f"  • {len(children)} Children")
        print(f"  • {len(products)} Products")
        print(f"  • {len(batches)} Batches")
        print(f"  • {len(meals)} Meals")
        print(f"  • {len(temperatures)} Temperatures")
        print(f"  • {len(equipments)} Equipments")
        print(f"  • {len(cleanings)} CleaningHaccp")
        print(f"  • {len(non_compliances)} NonCompliances")
        print(f"  • {len(documents)} Documents")
        print(f"  • {len(meal_children)} MealChildren associations")

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
