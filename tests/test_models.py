import pytest
from main import User, Performer, Room, TaskTemplate, AssignedTask
from main import UserRole, SessionStatus, LogStatus
import uuid

def test_user_creation(db_session):
    """Test de création d'un utilisateur"""
    user = User(
        firebase_uid="test-uid",
        full_name="Test User",
        role=UserRole.GERANTE
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.firebase_uid == "test-uid"
    assert user.full_name == "Test User"
    assert user.role == UserRole.GERANTE

def test_performer_creation(db_session):
    """Test de création d'un exécutant"""
    performer = Performer(name="Test Performer")
    db_session.add(performer)
    db_session.commit()
    
    assert performer.id is not None
    assert performer.name == "Test Performer"
    assert performer.is_active is True

def test_room_creation(db_session):
    """Test de création d'une pièce"""
    room = Room(
        name="Test Room",
        description="Test Description",
        display_order=1
    )
    db_session.add(room)
    db_session.commit()
    
    assert room.id is not None
    assert room.name == "Test Room"
    assert room.description == "Test Description"
    assert room.display_order == 1
    assert room.is_active is True

def test_task_template_creation(db_session):
    """Test de création d'un modèle de tâche"""
    task = TaskTemplate(
        name="Test Task",
        description="Test Description"
    )
    db_session.add(task)
    db_session.commit()
    
    assert task.id is not None
    assert task.name == "Test Task"
    assert task.description == "Test Description"
    assert task.is_active is True

def test_assigned_task_creation(db_session):
    """Test de création d'une tâche assignée"""
    # Créer les dépendances
    performer = Performer(name="Test Performer")
    room = Room(name="Test Room")
    task_template = TaskTemplate(name="Test Task")
    
    db_session.add(performer)
    db_session.add(room)
    db_session.add(task_template)
    db_session.commit()
    
    # Créer la tâche assignée
    assigned_task = AssignedTask(
        task_template_id=task_template.id,
        room_id=room.id,
        default_performer_id=performer.id,
        frequency_days=1,
        times_per_day=2
    )
    db_session.add(assigned_task)
    db_session.commit()
    
    assert assigned_task.id is not None
    assert assigned_task.frequency_days == 1
    assert assigned_task.times_per_day == 2
    assert assigned_task.is_active is True
