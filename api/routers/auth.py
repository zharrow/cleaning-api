import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import firebase_admin
from firebase_admin import auth as firebase_auth
import logging

from api.core.database import get_db
from api.models.user import Admin, User, UserRole
from api.schemas.user import UserResponse
from api.schemas.user_schemas import AdminResponse
# Import de get_current_user depuis security.py pour éviter la duplication
from api.core.security import get_current_user

logger = logging.getLogger(__name__)

# ✅ CORRIGÉ: Supprimer les tags ici car ils sont gérés dans main.py
router = APIRouter()

# Schémas Pydantic pour l'authentification
class LoginRequest(BaseModel):
    id_token: str  # Token Firebase

class LoginResponse(BaseModel):
    user: AdminResponse  # Changed from UserResponse to AdminResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RegisterRequest(BaseModel):
    id_token: str
    full_name: str
    role: UserRole = UserRole.MANAGER

async def verify_firebase_token(id_token: str) -> dict:
    """Vérifie un token Firebase et retourne les claims"""
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"Erreur vérification token Firebase: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Firebase invalide"
        )

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Connexion avec un token Firebase.
    
    - **id_token**: Token d'identification Firebase obtenu côté client
    
    Retourne les informations de l'utilisateur et un token d'accès.
    """
    # Vérifier le token Firebase
    decoded_token = await verify_firebase_token(login_data.id_token)
    firebase_uid = decoded_token['uid']
    email = decoded_token.get('email', '')

    # Rechercher l'admin par firebase_uid
    admin = db.query(Admin).filter(Admin.firebase_uid == firebase_uid).first()

    if not admin:
        # L'admin doit être créé par un développeur via l'interface admin
        # On ne peut pas auto-créer un admin sans created_by_id
        logger.warning(f"Tentative de connexion avec un compte Firebase non autorisé: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte non autorisé. Veuillez contacter l'administrateur système."
        )

    # Utiliser admin comme user pour compatibilité avec le reste du code
    user = admin

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # Log de connexion
    logger.info(
        f"Connexion réussie",
        extra={
            "user_id": str(user.id),
            "user_name": f"{user.first_name} {user.last_name}",
            "firebase_uid": firebase_uid
        }
    )

    return LoginResponse(
        user=AdminResponse.model_validate(user),
        access_token=login_data.id_token,  # On réutilise le token Firebase
        expires_in=3600
    )

@router.post("/register", response_model=UserResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Inscription d'un nouvel utilisateur.
    
    - **id_token**: Token Firebase pour vérifier l'identité
    - **full_name**: Nom complet de l'utilisateur
    - **role**: Rôle de l'utilisateur (par défaut: GERANTE)
    """
    # Vérifier le token Firebase
    decoded_token = await verify_firebase_token(register_data.id_token)
    firebase_uid = decoded_token['uid']
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur existe déjà"
        )
    
    # Créer le nouvel utilisateur
    new_user = User(
        firebase_uid=firebase_uid,
        full_name=register_data.full_name,
        role=register_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(
        f"Nouvel utilisateur inscrit",
        extra={
            "user_id": str(new_user.id),
            "user_name": new_user.full_name,
            "role": new_user.role.value
        }
    )
    
    return new_user

@router.get("/me", response_model=AdminResponse)
async def get_me(
    current_user: Admin = Depends(get_current_user)
):
    """
    Récupère les informations de l'admin connecté.

    Nécessite un token d'authentification valide.
    """
    return current_user

@router.put("/me", response_model=AdminResponse)
async def update_me(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour les informations de l'admin connecté.

    - **first_name**: Nouveau prénom (optionnel)
    - **last_name**: Nouveau nom (optionnel)
    """
    if first_name:
        current_user.first_name = first_name
    if last_name:
        current_user.last_name = last_name

    if first_name or last_name:
        current_user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(current_user)

        logger.info(
            f"Profil admin mis à jour",
            extra={
                "user_id": str(current_user.id),
                "user_name": f"{current_user.first_name} {current_user.last_name}"
            }
        )

    return current_user

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Rafraîchit le token d'accès avec un refresh token Firebase.
    
    - **refresh_token**: Refresh token Firebase
    """
    # Avec Firebase, on utilise leur système de refresh
    # Cette route est là pour la compatibilité
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Utilisez le SDK Firebase côté client pour rafraîchir les tokens"
    )

@router.post("/logout")
async def logout(
    current_user: Admin = Depends(get_current_user)
):
    """
    Déconnexion de l'admin.

    Note: Avec Firebase, la déconnexion se fait principalement côté client.
    Cette route peut être utilisée pour des actions côté serveur (logs, cleanup, etc.)
    """
    logger.info(
        f"Déconnexion",
        extra={
            "user_id": str(current_user.id),
            "user_name": f"{current_user.first_name} {current_user.last_name}"
        }
    )

    return {"message": "Déconnexion réussie"}

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime le compte de l'admin connecté.

    ⚠️ Cette action est irréversible!
    """
    logger.warning(
        f"Suppression de compte admin",
        extra={
            "user_id": str(current_user.id),
            "user_name": f"{current_user.first_name} {current_user.last_name}"
        }
    )

    # Supprimer l'admin de la base de données
    db.delete(current_user)
    db.commit()

    # Note: Il faudrait aussi supprimer l'utilisateur Firebase
    # mais cela nécessite l'Admin SDK avec des permissions élevées

    return None
