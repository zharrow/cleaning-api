import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from main import app, get_current_user, User

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