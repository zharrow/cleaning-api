import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from api.core.config import settings
from api.core.database import get_db
from api.models.user import User

logger = logging.getLogger(__name__)

# Initialisation Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_admin.initialize_app(cred)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency pour obtenir l'utilisateur actuel authentifié"""
    try:
        token = credentials.credentials
        logger.info(f"Token reçu: {token[:50]}...")
        
        decoded_token = firebase_auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        logger.info(f"Firebase UID décodé: {firebase_uid}")
        
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour firebase_uid: {firebase_uid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        logger.info(f"Utilisateur trouvé: {user.full_name} (ID: {user.id})")
        return user
    except Exception as e:
        logger.error(f"Erreur d'authentification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
