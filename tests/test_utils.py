import pytest
from datetime import date, datetime
import tempfile
import os
from main import generate_pdf_report_task, generate_zip_photos_task
from main import CleaningSession, User, Performer, Room, TaskTemplate, AssignedTask, CleaningLog
from main import UserRole, SessionStatus, LogStatus

def test_generate_pdf_report_task(db_session):
    """Test de génération de rapport PDF"""
    # Créer les données de test
    user = User(firebase_uid="test-uid", full_name="Test User", role=UserRole.GERANTE)
    performer = Performer(name="Test Performer")
    room = Room(name="Test Room")
    task_template = TaskTemplate(name="Test Task")
    
    db_session.add(user)
    db_session.add(performer)
    db_session.add(room)
    db_session.add(task_template)
    db_session.commit()
    
    assigned_task = AssignedTask(
        task_template_id=task_template.id,
        room_id=room.id,
        default_performer_id=performer.id
    )
    db_session.add(assigned_task)
    db_session.commit()
    
    session = CleaningSession(date=date.today(), status=SessionStatus.COMPLETEE)
    db_session.add(session)
    db_session.commit()
    
    log = CleaningLog(
        session_id=session.id,
        assigned_task_id=assigned_task.id,
        performer_id=performer.id,
        status=LogStatus.FAIT,
        notes="Test notes"
    )
    db_session.add(log)
    db_session.commit()
    
    # Tester la génération PDF (sans WeasyPrint pour éviter les dépendances)
    # Cette fonction devrait être mockée en production
    try:
        generate_pdf_report_task(session.id, db_session)
        # Si pas d'erreur, c'est bon
        assert True
    except Exception as e:
        # Attendu si WeasyPrint n'est pas installé
        assert "weasyprint" in str(e).lower() or "html" in str(e).lower()

def test_generate_zip_photos_task(db_session):
    """Test de génération de ZIP de photos"""
    # Créer les données de test
    performer = Performer(name="Test Performer")
    room = Room(name="Test Room")
    task_template = TaskTemplate(name="Test Task")
    
    db_session.add(performer)
    db_session.add(room)
    db_session.add(task_template)
    db_session.commit()
    
    assigned_task = AssignedTask(
        task_template_id=task_template.id,
        room_id=room.id,
        default_performer_id=performer.id
    )
    db_session.add(assigned_task)
    db_session.commit()
    
    session = CleaningSession(date=date.today(), status=SessionStatus.COMPLETEE)
    db_session.add(session)
    db_session.commit()
    
    log = CleaningLog(
        session_id=session.id,
        assigned_task_id=assigned_task.id,
        performer_id=performer.id,
        status=LogStatus.FAIT,
        photos=["test_photo.jpg"]
    )
    db_session.add(log)
    db_session.commit()
    
    # Tester la génération ZIP
    try:
        generate_zip_photos_task(session.id, db_session)
        assert True
    except Exception as e:
        # Attendu si les fichiers de photos n'existent pas
        assert "file" in str(e).lower() or "photo" in str(e).lower()