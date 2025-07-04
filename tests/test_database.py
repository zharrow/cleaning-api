import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, User, Performer, Room
from main import UserRole

def test_database_connection():
    """Test de connexion à la base de données"""
    # Test avec SQLite en mémoire
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Tester l'ajout d'un utilisateur
    user = User(
        firebase_uid="test-uid",
        full_name="Test User",
        role=UserRole.GERANTE
    )
    session.add(user)
    session.commit()
    
    # Vérifier que l'utilisateur a été ajouté
    users = session.query(User).all()
    assert len(users) == 1
    assert users[0].firebase_uid == "test-uid"
    
    session.close()

def test_relationships(db_session):
    """Test des relations entre tables"""
    # Créer les entités
    performer = Performer(name="Test Performer")
    room = Room(name="Test Room")
    
    db_session.add(performer)
    db_session.add(room)
    db_session.commit()
    
    # Vérifier que les IDs ont été générés
    assert performer.id is not None
    assert room.id is not None
    
    # Tester les requêtes
    found_performer = db_session.query(Performer).filter(Performer.name == "Test Performer").first()
    assert found_performer is not None
    assert found_performer.name == "Test Performer"