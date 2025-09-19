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
