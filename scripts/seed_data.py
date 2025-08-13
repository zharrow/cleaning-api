#!/usr/bin/env python3
"""
Script pour remplir la base de données avec des données de test
"""
import asyncio
from datetime import date, datetime, timedelta
import random
from faker import Faker
from sqlalchemy.orm import Session

from api.core.database import SessionLocal, engine
from api.models.user import User, UserRole
from api.models.performer import Performer
from api.models.room import Room
from api.models.task import TaskTemplate, AssignedTask
from api.models.session import CleaningSession, SessionStatus
from api.models.cleaning_log import CleaningLog, LogStatus
from api.models import *

faker = Faker('fr_FR')

def seed_database():
    """Remplit la base de données avec des données de test"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding database...")
        
        # Créer des utilisateurs
        users = []
        for i in range(3):
            user = User(
                firebase_uid=f"test-uid-{i}",
                full_name=faker.name(),
                role=UserRole.GERANTE
            )
            db.add(user)
            users.append(user)
        
        # Créer des exécutants
        performers = []
        for _ in range(5):
            performer = Performer(
                name=faker.name(),
                is_active=random.choice([True, True, True, False])
            )
            db.add(performer)
            performers.append(performer)
        
        # Créer des pièces
        rooms_data = [
            ("Salle de jeu", "Espace principal d'activité"),
            ("Dortoir", "Espace de sieste"),
            ("Cuisine", "Préparation des repas"),
            ("Salle de bain enfants", "Sanitaires adaptés"),
            ("Salle de change", "Espace de change"),
            ("Bureau", "Administration"),
            ("Salle du personnel", "Espace repos personnel"),
            ("Entrée", "Hall d'accueil"),
            ("Cour extérieure", "Espace de jeu extérieur")
        ]
        
        rooms = []
        for i, (name, desc) in enumerate(rooms_data):
            room = Room(
                name=name,
                description=desc,
                display_order=i,
                is_active=True
            )
            db.add(room)
            rooms.append(room)
        
        # Créer des modèles de tâches
        tasks_data = [
            ("Désinfecter les surfaces", "Nettoyer et désinfecter toutes les surfaces"),
            ("Aspirer les sols", "Passer l'aspirateur dans toute la pièce"),
            ("Laver les sols", "Nettoyer les sols à l'eau"),
            ("Vider les poubelles", "Évacuer tous les déchets"),
            ("Nettoyer les vitres", "Laver fenêtres et miroirs"),
            ("Désinfecter les jouets", "Nettoyer tous les jouets"),
            ("Nettoyer les WC", "Désinfecter complètement les toilettes"),
            ("Ranger la pièce", "Remettre en ordre"),
            ("Laver le linge", "Machine à laver et séchage"),
            ("Désinfecter les poignées", "Nettoyer poignées et interrupteurs"),
            ("Nettoyer les tables", "Désinfecter les surfaces de repas"),
            ("Vérifier les stocks", "Contrôler produits d'entretien")
        ]
        
        task_templates = []
        for name, desc in tasks_data:
            task = TaskTemplate(
                name=name,
                description=desc,
                is_active=True
            )
            db.add(task)
            task_templates.append(task)
        
        db.commit()
        
        # Créer des tâches assignées
        for room in rooms[:6]:  # Principales pièces
            for task in random.sample(task_templates, k=random.randint(3, 6)):
                assigned = AssignedTask(
                    task_template_id=task.id,
                    room_id=room.id,
                    default_performer_id=random.choice(performers).id,
                    frequency_days=random.choice([1, 1, 1, 2, 7]),
                    times_per_day=random.choice([1, 1, 2, 3]),
                    is_active=True
                )
                db.add(assigned)
        
        db.commit()
        
        # Créer des sessions et logs pour les 30 derniers jours
        for days_ago in range(30):
            session_date = date.today() - timedelta(days=days_ago)
            
            session = CleaningSession(
                date=session_date,
                status=random.choice([
                    SessionStatus.COMPLETEE,
                    SessionStatus.COMPLETEE,
                    SessionStatus.INCOMPLETE
                ]) if days_ago > 0 else SessionStatus.EN_COURS
            )
            db.add(session)
            db.commit()
            
            # Créer des logs pour cette session
            assigned_tasks = db.query(AssignedTask).filter(AssignedTask.is_active == True).all()
            for task in random.sample(assigned_tasks, k=random.randint(10, len(assigned_tasks))):
                log = CleaningLog(
                    session_id=session.id,
                    assigned_task_id=task.id,
                    performer_id=random.choice(performers).id,
                    status=random.choice([
                        LogStatus.FAIT,
                        LogStatus.FAIT,
                        LogStatus.FAIT,
                        LogStatus.PARTIEL,
                        LogStatus.REPORTE
                    ]),
                    notes=faker.sentence() if random.random() > 0.7 else None,
                    timestamp=datetime.combine(
                        session_date,
                        datetime.now().time().replace(
                            hour=random.randint(6, 18),
                            minute=random.randint(0, 59)
                        )
                    )
                )
                db.add(log)
            
            db.commit()
        
        print("✅ Database seeded successfully!")
        print(f"📊 Created:")
        print(f"   - {len(users)} users")
        print(f"   - {len(performers)} performers")
        print(f"   - {len(rooms)} rooms")
        print(f"   - {len(task_templates)} task templates")
        print(f"   - 30 cleaning sessions with logs")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()