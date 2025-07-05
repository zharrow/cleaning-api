import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from api.main import app
from api.core.database import get_db, Base
from api.models import User, Performer, Room, etc
from api.models.user import UserRole
from api.models.performer import Performer
from api.models.room import Room
from api.models.task_template import TaskTemplate
from api.models.assigned_task import AssignedTask
from api.models.cleaning_session import CleaningSession, SessionStatus
from api.models.cleaning_log import CleaningLog, LogStatus

def test_auth_no_token():
    """Test sans token d'authentification"""
    client = TestClient(app)
    response = client.get("/users/me")
    assert response.status_code == 403  # Forbidden sans token

@patch('firebase_admin.auth.verify_id_token')
def test_auth_invalid_token(mock_verify):
    """Test avec token invalide"""
    mock_verify.side_effect = Exception("Invalid token")
    
    client = TestClient(app)
    response = client.get("/users/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401

@patch('firebase_admin.auth.verify_id_token')
def test_auth_valid_token_no_user(mock_verify, db_session):
    """Test avec token valide mais utilisateur non trouvé"""
    mock_verify.return_value = {"uid": "non-existent-uid"}
    
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    response = client.get("/users/me", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 401