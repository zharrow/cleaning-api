"""
Script d'initialisation de la base de données SANS Alembic
Usage: python init_db.py
"""
import asyncio
from sqlalchemy import create_engine
from api.core.database import Base, engine  
from api.core.config import settings
from api.models import *  # Import tous les modèles
from sqlalchemy.orm import sessionmaker
import uuid

def create_tables():
    """Crée toutes les tables directement avec SQLAlchemy"""
    print("🏗️ Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès")

def populate_initial_data():
    """Ajoute des données initiales"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from api.models.user import User, UserRole
        from api.models.performer import Performer
        from api.models.room import Room
        from api.models.task import TaskTemplate
        
        # Vérifier si des données existent déjà
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("ℹ️ Des données existent déjà, pas d'initialisation")
            return
        
        print("🌱 Ajout des données initiales...")
        
        # Créer un utilisateur administrateur de test
        admin_user = User(
            id=str(uuid.uuid4()),
            firebase_uid="admin_test_uid",
            full_name="Administrateur Test",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.flush()  # Pour obtenir l'ID
        
        # Exécutants par défaut
        performers_data = [
            {"first_name": "Marie", "last_name": "Dupont", "email": "marie.dupont@exemple.fr"},
            {"first_name": "Jean", "last_name": "Martin", "email": "jean.martin@exemple.fr"},
            {"first_name": "Sophie", "last_name": "Leroux", "email": "sophie.leroux@exemple.fr"},
        ]
        
        for performer_data in performers_data:
            performer = Performer(
                id=str(uuid.uuid4()),
                first_name=performer_data["first_name"],
                last_name=performer_data["last_name"],
                email=performer_data["email"],
                manager_id=admin_user.id,
                is_active=True
            )
            db.add(performer)
        
        # Pièces par défaut
        rooms_data = [
            {"name": "Salle de jeu", "description": "Espace principal d'activité", "display_order": 1},
            {"name": "Cuisine", "description": "Préparation des repas", "display_order": 2},
            {"name": "Salle de bain", "description": "Sanitaires et change", "display_order": 3},
            {"name": "Entrée", "description": "Hall d'accueil", "display_order": 4},
            {"name": "Extérieur", "description": "Cour et jardin", "display_order": 5},
        ]
        
        for room_data in rooms_data:
            room = Room(
                id=str(uuid.uuid4()),
                **room_data,
                is_active=True
            )
            db.add(room)
        
        # Tâches par défaut
        tasks_data = [
            {"title": "Désinfecter les surfaces", "description": "Nettoyer et désinfecter toutes les surfaces"},
            {"title": "Aspirer/Balayer", "description": "Nettoyage des sols"},
            {"title": "Vider les poubelles", "description": "Évacuer les déchets"},
            {"title": "Nettoyer les vitres", "description": "Nettoyage des fenêtres et miroirs"},
            {"title": "Désinfecter les jouets", "description": "Nettoyage et désinfection des jouets"},
            {"title": "Nettoyer les WC", "description": "Nettoyage complet des sanitaires"},
            {"title": "Laver le linge", "description": "Lavage du linge de la crèche"},
        ]
        
        for task_data in tasks_data:
            task = TaskTemplate(
                id=str(uuid.uuid4()),
                **task_data,
                is_active=True
            )
            db.add(task)
        
        db.commit()
        print("✅ Données initiales ajoutées avec succès")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de l'ajout des données: {e}")
        raise
    finally:
        db.close()

def main():
    """Fonction principale d'initialisation"""
    print("🚀 Initialisation de la base de données (SQLAlchemy direct)...")
    
    # Créer les tables
    create_tables()
    
    # Ajouter les données initiales
    populate_initial_data()
    
    print("✅ Initialisation terminée!")
    print("\n📝 Prochaines étapes:")
    print("1. Configurer les tâches assignées via l'API")
    print("2. Créer les utilisateurs Firebase")
    print("3. Démarrer l'application: python -m api.main")

if __name__ == "__main__":
    main()