"""
Script d'initialisation de la base de données
Usage: python init_db.py
"""
import asyncio
from sqlalchemy import create_engine
from api.core.database import Base, engine  
from api.core.config import settings
from api.models import User, Performer, Room, TaskTemplate, AssignedTask
from sqlalchemy.orm import sessionmaker
from decouple import config
import uuid

def create_tables():
    """Crée toutes les tables"""
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès")

def populate_initial_data():
    """Ajoute des données initiales"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Exécutants par défaut
        performers = [
            {"name": "Marie Dupont"},
            {"name": "Jean Martin"},
            {"name": "Sophie Leroux"},
        ]
        
        for performer_data in performers:
            existing = db.query(Performer).filter(Performer.name == performer_data["name"]).first()
            if not existing:
                performer = Performer(**performer_data)
                db.add(performer)
        
        # Pièces par défaut
        rooms = [
            {"name": "Salle de jeu", "description": "Espace principal d'activité", "display_order": 1},
            {"name": "Cuisine", "description": "Préparation des repas", "display_order": 2},
            {"name": "Salle de bain", "description": "Sanitaires et change", "display_order": 3},
            {"name": "Entrée", "description": "Hall d'accueil", "display_order": 4},
            {"name": "Extérieur", "description": "Cour et jardin", "display_order": 5},
        ]
        
        for room_data in rooms:
            existing = db.query(Room).filter(Room.name == room_data["name"]).first()
            if not existing:
                room = Room(**room_data)
                db.add(room)
        
        # Tâches par défaut
        tasks = [
            {"name": "Désinfecter les surfaces", "description": "Nettoyer et désinfecter toutes les surfaces"},
            {"name": "Aspirer/Balayer", "description": "Nettoyage des sols"},
            {"name": "Vider les poubelles", "description": "Évacuer les déchets"},
            {"name": "Nettoyer les vitres", "description": "Nettoyage des fenêtres et miroirs"},
            {"name": "Désinfecter les jouets", "description": "Nettoyage et désinfection des jouets"},
            {"name": "Nettoyer les WC", "description": "Nettoyage complet des sanitaires"},
            {"name": "Laver le linge", "description": "Lavage du linge de la crèche"},
        ]
        
        for task_data in tasks:
            existing = db.query(TaskTemplate).filter(TaskTemplate.name == task_data["name"]).first()
            if not existing:
                task = TaskTemplate(**task_data)
                db.add(task)
        
        db.commit()
        print("✅ Données initiales ajoutées avec succès")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de l'ajout des données: {e}")
    finally:
        db.close()

def main():
    """Fonction principale d'initialisation"""
    print("🚀 Initialisation de la base de données...")
    
    # Créer les tables
    create_tables()
    
    # Ajouter les données initiales
    populate_initial_data()
    
    print("✅ Initialisation terminée!")
    print("\n📝 Prochaines étapes:")
    print("1. Configurer les tâches assignées via l'API")
    print("2. Créer les utilisateurs Firebase")
    print("3. Démarrer l'application: uvicorn main:app --reload")

if __name__ == "__main__":
    main()