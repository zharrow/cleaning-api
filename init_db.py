"""
Script d'initialisation de la base de données avec types UUID cohérents
Crée des données d'exemple réalistes pour tester l'application
Usage: python init_db.py
"""
import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal

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

        # Import de tous les modèles cLean
        from api.models.user import User
        from api.models.performer import Performer
        from api.models.room import Room
        from api.models.task import TaskTemplate, AssignedTask
        from api.models.session import CleaningSession
        from api.models.cleaning_log import CleaningLog
        from api.models.export import Export
        from api.models.enterprise import Enterprise

        # Import des modèles HACCP
        from api.models.haccp_models import (
            Child, Supplier, Product, Batch, Meal, Temperature,
            Equipment, CleaningHaccp, NonCompliance, Document, MealChildren
        )

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
    """Crée des données d'exemple réalistes pour cLean + HACCP"""
    try:
        print("Creation de donnees d'exemple completes...")

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from api.models.user import User, UserRole
        from api.models.performer import Performer
        from api.models.room import Room
        from api.models.task import TaskTemplate, TaskType, AssignedTask
        from api.models.enterprise import Enterprise

        # HACCP models
        from api.models.haccp_models import (
            Child, Supplier, Product, Batch, Meal, Temperature,
            Equipment, CleaningHaccp, NonCompliance, Document,
            Section, MealType, Checkpoint, CleaningFrequency,
            NonComplianceType, NonComplianceStatus, DocumentCategory
        )

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

            print("→ Creation utilisateur et entreprise...")
            # Créer un utilisateur test (admin/gérant)
            test_user = User(
                firebase_uid="test-uid-123456",
                full_name="Claire Martin",
                role=UserRole.GERANTE
            )
            db.add(test_user)
            db.flush()

            # Créer une entreprise liée à l'utilisateur
            enterprise = Enterprise(
                user_id=test_user.id,
                name="Micro-Crèche Les Petits Lutins",
                legal_form="SARL",
                siret="12345678901234"
            )
            db.add(enterprise)
            db.flush()
            print(f"  ✓ Entreprise créée: {enterprise.name}")

            # ==================== cLEAN MODULE ====================

            print("→ Creation performers (employés)...")
            performers_data = [
                "Marie Dupont",
                "Sophie Bernard",
                "Julie Rousseau",
                "Emma Moreau"
            ]

            performers = []
            for name in performers_data:
                performer = Performer(
                    name=name,
                    created_by_id=test_user.id
                )
                db.add(performer)
                performers.append(performer)
            db.flush()
            print(f"  ✓ {len(performers)} employés créés")

            print("→ Creation pièces...")
            rooms_data = [
                ("Salle de jeu - Bébés", "Espace d'éveil pour les tout-petits (0-18 mois)", 1),
                ("Salle de jeu - Moyens", "Activités pour les enfants de 18-36 mois", 2),
                ("Cuisine", "Préparation et réchauffage des repas", 3),
                ("Salle de repas", "Espace dédié aux repas", 4),
                ("Salle de sieste", "Dortoir avec lits bébés", 5),
                ("Salle de bain", "Sanitaires et espace de change", 6),
                ("Entrée/Hall", "Hall d'accueil des parents", 7)
            ]

            rooms = []
            for name, desc, order in rooms_data:
                room = Room(
                    name=name,
                    description=desc,
                    display_order=order
                )
                db.add(room)
                rooms.append(room)
            db.flush()
            print(f"  ✓ {len(rooms)} pièces créées")

            print("→ Creation modèles de tâches...")
            tasks_data = [
                ("Désinfecter les surfaces", "Nettoyer et désinfecter tables, chaises, plans de travail", TaskType.DAILY, 15),
                ("Aspirer et laver les sols", "Aspiration puis lavage à l'eau et désinfectant", TaskType.DAILY, 20),
                ("Désinfecter les jouets", "Nettoyer tous les jouets utilisés dans la journée", TaskType.DAILY, 25),
                ("Vider les poubelles", "Évacuer les déchets et remplacer les sacs", TaskType.DAILY, 5),
                ("Nettoyer les vitres", "Nettoyage des fenêtres et baies vitrées", TaskType.WEEKLY, 30),
                ("Désinfecter les lits", "Nettoyage complet des lits et matelas", TaskType.WEEKLY, 20),
                ("Nettoyer les réfrigérateurs", "Nettoyage intérieur des frigos", TaskType.WEEKLY, 15),
                ("Aérer les pièces", "Ouvrir les fenêtres 10 minutes", TaskType.DAILY, 10),
                ("Contrôler les stocks de produits", "Vérifier les produits d'entretien", TaskType.MONTHLY, 15)
            ]

            task_templates = []
            for title, desc, task_type, duration in tasks_data:
                task = TaskTemplate(
                    name=title,
                    description=desc,
                    type=task_type,
                    default_duration=duration,
                    estimated_duration=duration
                )
                db.add(task)
                task_templates.append(task)
            db.flush()
            print(f"  ✓ {len(task_templates)} modèles de tâches créés")

            print("→ Assignation de tâches aux pièces...")
            # Assigner quelques tâches aux pièces
            assignments = [
                (rooms[0], task_templates[0], performers[0]),  # Salle jeu bébés - Désinfecter
                (rooms[0], task_templates[1], performers[1]),  # Salle jeu bébés - Aspirer
                (rooms[1], task_templates[0], performers[0]),  # Salle jeu moyens - Désinfecter
                (rooms[1], task_templates[2], performers[2]),  # Salle jeu moyens - Jouets
                (rooms[2], task_templates[0], performers[1]),  # Cuisine - Surfaces
                (rooms[2], task_templates[6], performers[1]),  # Cuisine - Frigos
                (rooms[3], task_templates[1], performers[3]),  # Salle repas - Sols
                (rooms[4], task_templates[5], performers[2]),  # Sieste - Lits
                (rooms[5], task_templates[0], performers[3]),  # Salle de bain
                (rooms[6], task_templates[3], performers[0]),  # Entrée - Poubelles
            ]

            for room, task, performer in assignments:
                assigned = AssignedTask(
                    room_id=room.id,
                    task_template_id=task.id,
                    default_performer_id=performer.id,
                    frequency={"type": "daily"} if task.type == TaskType.DAILY else {"type": "weekly", "day": "monday"},
                    expected_duration=task.default_duration,
                    is_active=True
                )
                db.add(assigned)
            db.flush()
            print(f"  ✓ {len(assignments)} tâches assignées")

            # ==================== HACCP MODULE ====================

            print("→ Creation fournisseurs HACCP...")
            suppliers_data = [
                ("Sodexo Petite Enfance", "Marie Legrand", "01 23 45 67 89", "contact@sodexo.fr", True),
                ("Bio Bébé Alimentation", "Pierre Dubois", "01 98 76 54 32", "commandes@biobebe.fr", True),
                ("Fruits & Légumes Bio du Coin", "Sophie Martin", "06 12 34 56 78", "bio@legumes-frais.fr", False)
            ]

            suppliers = []
            for name, contact, phone, email, haccp in suppliers_data:
                supplier = Supplier(
                    enterprise_id=enterprise.id,
                    name=name,
                    contact_name=contact,
                    phone=phone,
                    email=email,
                    haccp_certified=haccp,
                    validation_date=date.today() - timedelta(days=30) if haccp else None
                )
                db.add(supplier)
                suppliers.append(supplier)
            db.flush()
            print(f"  ✓ {len(suppliers)} fournisseurs créés")

            print("→ Creation produits alimentaires...")
            products_data = [
                ("Purée de carottes bio", "Légumes", "Céleri", suppliers[1]),
                ("Compote de pommes", "Fruits", "", suppliers[1]),
                ("Yaourt nature", "Produits laitiers", "Lait, lactose", suppliers[0]),
                ("Blanc de poulet", "Viande", "", suppliers[0]),
                ("Pâtes alphabet", "Féculents", "Gluten", suppliers[0]),
                ("Petits pois surgelés", "Légumes", "", suppliers[2]),
                ("Fromage blanc", "Produits laitiers", "Lait, lactose", suppliers[0]),
                ("Jambon blanc", "Viande", "", suppliers[0])
            ]

            products = []
            for name, category, allergens, supplier in products_data:
                product = Product(
                    enterprise_id=enterprise.id,
                    supplier_id=supplier.id,
                    name=name,
                    category=category,
                    allergens=allergens if allergens else None,
                    stock_unit="unité",
                    current_stock=Decimal("10.0"),
                    expiry_date=date.today() + timedelta(days=30)
                )
                db.add(product)
                products.append(product)
            db.flush()
            print(f"  ✓ {len(products)} produits créés")

            print("→ Creation lots de produits...")
            for i, product in enumerate(products[:4]):  # Quelques lots pour exemples
                batch = Batch(
                    product_id=product.id,
                    batch_code=f"LOT2025{1000+i}",
                    reception_date=date.today() - timedelta(days=i),
                    received_quantity=Decimal("50.0"),
                    reception_temperature=Decimal("4.5") if product.category in ["Produits laitiers", "Viande"] else None,
                    is_compliant=True,
                    observations="Conforme à la réception"
                )
                db.add(batch)
            db.flush()
            print(f"  ✓ 4 lots de produits créés")

            print("→ Creation enfants...")
            children_data = [
                ("Léo", "Martin", date(2023, 3, 15), Section.BABIES, "", ""),
                ("Emma", "Bernard", date(2023, 1, 8), Section.BABIES, "Lactose", "Sans lait de vache"),
                ("Lucas", "Dubois", date(2022, 6, 20), Section.TODDLERS, "", ""),
                ("Chloé", "Petit", date(2022, 9, 12), Section.TODDLERS, "Arachides, fruits à coques", "Éviter toutes traces de noix"),
                ("Noah", "Roux", date(2021, 11, 5), Section.PRESCHOOLERS, "", ""),
                ("Inès", "Moreau", date(2022, 2, 28), Section.TODDLERS, "Gluten", "Maladie cœliaque - sans gluten"),
                ("Louis", "Simon", date(2023, 5, 10), Section.BABIES, "", ""),
                ("Zoé", "Laurent", date(2022, 4, 17), Section.TODDLERS, "", "Végétarien")
            ]

            children = []
            for first, last, birth, section, allergies, diet in children_data:
                child = Child(
                    enterprise_id=enterprise.id,
                    first_name=first,
                    last_name=last,
                    birth_date=birth,
                    section=section,
                    allergies=allergies if allergies else None,
                    specific_diet=diet if diet else None,
                    is_active=True
                )
                db.add(child)
                children.append(child)
            db.flush()
            print(f"  ✓ {len(children)} enfants créés")

            print("→ Creation repas de la semaine...")
            # Repas d'aujourd'hui et hier
            meals = []
            for day_offset in range(2):
                meal_date = date.today() - timedelta(days=day_offset)

                # Petit-déjeuner
                breakfast = Meal(
                    enterprise_id=enterprise.id,
                    supplier_id=suppliers[0].id,
                    responsible_id=test_user.id,
                    date=meal_date,
                    meal_type=MealType.BREAKFAST,
                    description="Yaourt nature + compote de pommes + tartine de pain"
                )
                db.add(breakfast)
                meals.append(breakfast)

                # Déjeuner
                lunch = Meal(
                    enterprise_id=enterprise.id,
                    supplier_id=suppliers[0].id,
                    responsible_id=test_user.id,
                    date=meal_date,
                    meal_type=MealType.LUNCH,
                    description="Blanc de poulet + purée de carottes + yaourt"
                )
                db.add(lunch)
                meals.append(lunch)

                # Goûter
                snack = Meal(
                    enterprise_id=enterprise.id,
                    supplier_id=suppliers[1].id,
                    responsible_id=test_user.id,
                    date=meal_date,
                    meal_type=MealType.SNACK,
                    description="Compote de pommes + biscuit"
                )
                db.add(snack)
                meals.append(snack)

            db.flush()
            print(f"  ✓ {len(meals)} repas créés")

            print("→ Creation contrôles température...")
            # Températures pour le déjeuner d'aujourd'hui
            today_lunch = [m for m in meals if m.date == date.today() and m.meal_type == MealType.LUNCH][0]

            checkpoints_data = [
                (Checkpoint.RECEPTION, Decimal("3.5"), True, "Livraison conforme"),
                (Checkpoint.STORAGE, Decimal("4.0"), True, "Stockage frigo OK"),
                (Checkpoint.HOLDING, Decimal("65.0"), True, "Maintien en température"),
                (Checkpoint.SERVICE, Decimal("63.0"), True, "Service aux enfants")
            ]

            for checkpoint, temp, compliant, obs in checkpoints_data:
                temperature = Temperature(
                    meal_id=today_lunch.id,
                    responsible_id=test_user.id,
                    checkpoint=checkpoint,
                    temperature=temp,
                    is_compliant=compliant,
                    observations=obs,
                    control_date=datetime.now() - timedelta(hours=4-checkpoints_data.index((checkpoint, temp, compliant, obs)))
                )
                db.add(temperature)
            db.flush()
            print(f"  ✓ 4 contrôles de température créés")

            print("→ Creation équipements cuisine...")
            equipment_data = [
                ("Réfrigérateur principal", "Fridge", Decimal("4.0"), True),
                ("Congélateur", "Freezer", Decimal("-18.0"), True),
                ("Four électrique", "Oven", None, True),
                ("Chauffe-biberon", "Warmer", None, True),
                ("Micro-ondes", "Microwave", None, False)  # Nécessite maintenance
            ]

            for name, eq_type, target_temp, compliant in equipment_data:
                equipment = Equipment(
                    enterprise_id=enterprise.id,
                    name=name,
                    type=eq_type,
                    last_control_date=date.today() - timedelta(days=15),
                    target_temperature=target_temp,
                    is_compliant=compliant,
                    observations="Maintenance annuelle planifiée" if not compliant else "Fonctionnement normal"
                )
                db.add(equipment)
            db.flush()
            print(f"  ✓ {len(equipment_data)} équipements créés")

            print("→ Creation registres de nettoyage HACCP...")
            cleaning_zones = [
                ("Plan de travail cuisine", "Détergent professionnel", CleaningFrequency.DAILY),
                ("Réfrigérateur intérieur", "Désinfectant alimentaire", CleaningFrequency.WEEKLY),
                ("Sol de la cuisine", "Détergent + désinfectant", CleaningFrequency.DAILY),
                ("Poignées de portes cuisine", "Solution hydroalcoolique", CleaningFrequency.DAILY)
            ]

            for zone, product, freq in cleaning_zones:
                cleaning = CleaningHaccp(
                    enterprise_id=enterprise.id,
                    responsible_id=test_user.id,
                    zone=zone,
                    product_used=product,
                    frequency=freq,
                    cleaning_date=datetime.now() - timedelta(hours=2),
                    observations="Nettoyage conforme au protocole"
                )
                db.add(cleaning)
            db.flush()
            print(f"  ✓ {len(cleaning_zones)} registres de nettoyage créés")

            print("→ Creation document HACCP...")
            doc = Document(
                enterprise_id=enterprise.id,
                responsible_id=test_user.id,
                name="Relevé des températures - Janvier 2025",
                category=DocumentCategory.TEMPERATURES,
                file_path="/documents/temperatures_jan2025.pdf",
                creation_date=date.today(),
                retention_period="3 ans"
            )
            db.add(doc)
            db.flush()
            print(f"  ✓ 1 document créé")

            # Lier les enfants aux repas d'aujourd'hui
            print("→ Association enfants/repas...")
            today_meals = [m for m in meals if m.date == date.today()]
            for meal in today_meals:
                for child in children:
                    # Tous les enfants ne mangent pas forcément tous les repas
                    if meal.meal_type == MealType.BREAKFAST and child.section == Section.BABIES:
                        continue  # Les bébés ne prennent pas le petit-déj à la crèche

                    from api.models.haccp_models import MealChildren
                    meal_child = MealChildren(
                        meal_id=meal.id,
                        child_id=child.id,
                        portion="Normale" if child.section != Section.BABIES else "Petite",
                        observations="RAS"
                    )
                    db.add(meal_child)
            db.flush()
            print(f"  ✓ Associations repas/enfants créées")

            db.commit()

            print("\n" + "="*60)
            print("SUCCESS - Données d'exemple complètes créées!")
            print("="*60)
            print(f"\n📊 RÉSUMÉ:")
            print(f"  • Entreprise: {enterprise.name}")
            print(f"  • Employés: {len(performers)}")
            print(f"  • Pièces: {len(rooms)}")
            print(f"  • Modèles de tâches: {len(task_templates)}")
            print(f"  • Tâches assignées: {len(assignments)}")
            print(f"  • Fournisseurs: {len(suppliers)}")
            print(f"  • Produits: {len(products)}")
            print(f"  • Enfants: {len(children)}")
            print(f"  • Repas: {len(meals)}")
            print(f"  • Contrôles température: 4")
            print(f"  • Équipements: {len(equipment_data)}")
            print(f"  • Registres nettoyage HACCP: {len(cleaning_zones)}")

            return True

        except Exception as e:
            db.rollback()
            print(f"ERREUR - Erreur creation donnees d'exemple: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    except Exception as e:
        print(f"ERREUR - Erreur donnees d'exemple: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale d'initialisation"""
    print("="*60)
    print("Initialisation de la base de donnees avec UUID...")
    print("="*60)

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
    if not create_sample_data():
        print("ERREUR - Echec de la creation des donnees")
        sys.exit(1)

    print("\n" + "="*60)
    print("SUCCESS - Initialisation terminee!")
    print("="*60)
    print("\n📍 Services disponibles:")
    print("  1. API: http://localhost:8000")
    print("  2. Documentation: http://localhost:8000/docs")
    print("  3. Interface DB: http://localhost:8080")
    print("\n🔑 Utilisateur test:")
    print("  • Email: test (via Firebase)")
    print("  • UID: test-uid-123456")
    print("  • Rôle: GERANTE")
    print("  • Entreprise: Micro-Crèche Les Petits Lutins")

if __name__ == "__main__":
    main()
