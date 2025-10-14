import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from api.core.config import settings
from api.core.database import get_db
from api.models.user import User, Admin, Developer

logger = logging.getLogger(__name__)

# Initialisation Firebase
if not firebase_admin._apps:
    import os
    import base64
    import json
    import tempfile

    cred = None

    # Mode production : Firebase credentials encodés en base64
    if settings.firebase_credentials_base64:
        try:
            # Décoder le base64 pour récupérer le JSON
            credentials_json = base64.b64decode(settings.firebase_credentials_base64).decode('utf-8')
            credentials_dict = json.loads(credentials_json)

            # Créer un fichier temporaire avec les credentials
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(credentials_dict, temp_file)
                temp_file_path = temp_file.name

            cred = credentials.Certificate(temp_file_path)

            # Nettoyer le fichier temporaire après initialisation
            os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Erreur décodage Firebase credentials base64: {e}")
            raise RuntimeError(f"Credentials Firebase base64 invalides: {e}")

    # Mode développement : fichier JSON local
    elif settings.firebase_credentials_path and os.path.exists(settings.firebase_credentials_path):
        cred = credentials.Certificate(settings.firebase_credentials_path)

    else:
        raise RuntimeError(
            "Configuration Firebase manquante. "
            "En production: définissez FIREBASE_CREDENTIALS_BASE64 "
            "En développement: placez firebase-credentials.json et définissez FIREBASE_CREDENTIALS_PATH"
        )

    firebase_admin.initialize_app(cred)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """
    LEGACY: Dependency pour obtenir l'utilisateur actuel authentifié
    NOTE: This is for backward compatibility only. Use get_current_admin for new code.
    UPDATED: Now returns Admin instead of User (User model is for employees with PIN auth)
    """
    try:
        token = credentials.credentials
        logger.info(f"Token reçu: {token[:50]}...")

        decoded_token = firebase_auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        logger.info(f"Firebase UID décodé: {firebase_uid}")

        # Chercher un Admin (Firebase Auth)
        admin = db.query(Admin).filter(Admin.firebase_uid == firebase_uid).first()
        if not admin:
            logger.warning(f"Admin non trouvé pour firebase_uid: {firebase_uid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )

        if not admin.is_active:
            logger.warning(f"Admin inactif tenté d'accéder: {admin.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte désactivé"
            )

        logger.info(f"Admin trouvé: {admin.first_name} {admin.last_name} (ID: {admin.id})")
        return admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur d'authentification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """
    Multi-tier authentication: Get current Admin (daycare manager) from Firebase token
    """
    try:
        token = credentials.credentials
        logger.info(f"Admin token received: {token[:50]}...")

        decoded_token = firebase_auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        logger.info(f"Admin Firebase UID: {firebase_uid}")

        admin = db.query(Admin).filter(Admin.firebase_uid == firebase_uid).first()
        if not admin:
            logger.warning(f"Admin not found for firebase_uid: {firebase_uid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin non trouvé"
            )

        if not admin.is_active:
            logger.warning(f"Inactive admin attempted access: {admin.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte administrateur désactivé"
            )

        logger.info(f"Admin authenticated: {admin.first_name} {admin.last_name} (ID: {admin.id})")
        return admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )


async def get_current_developer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Developer:
    """
    Multi-tier authentication: Get current Developer (super admin) from Firebase token
    """
    try:
        token = credentials.credentials
        logger.info(f"Developer token received: {token[:50]}...")

        decoded_token = firebase_auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        logger.info(f"Developer Firebase UID: {firebase_uid}")

        developer = db.query(Developer).filter(Developer.firebase_uid == firebase_uid).first()
        if not developer:
            logger.warning(f"Developer not found for firebase_uid: {firebase_uid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Developer non trouvé"
            )

        logger.info(f"Developer authenticated: {developer.email} (ID: {developer.id})")
        return developer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Developer authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
