"""
Configuration et initialisation Firebase Admin SDK
"""

import os
import logging
import firebase_admin
from firebase_admin import credentials
from pathlib import Path

logger = logging.getLogger(__name__)


class FirebaseManager:
    """Gestionnaire pour l'initialisation de Firebase Admin SDK"""
    
    def __init__(self):
        self.initialized = False
        self.app = None
    
    def initialize_firebase(self) -> bool:
        """Initialise Firebase Admin SDK avec les credentials"""
        
        if self.initialized:
            logger.info("Firebase déjà initialisé")
            return True
        
        try:
            # Chemin vers le fichier de credentials
            credentials_path = Path("firebase-credentials.json")
            
            if not credentials_path.exists():
                logger.error(f"Fichier credentials non trouvé: {credentials_path}")
                return False
            
            # Initialiser Firebase Admin SDK
            cred = credentials.Certificate(str(credentials_path))
            self.app = firebase_admin.initialize_app(cred, {
                'storageBucket': 'cleaning-app-toulouse.appspot.com'
            })
            
            self.initialized = True
            logger.info("Firebase Admin SDK initialisé avec succès")
            return True
            
        except ValueError as e:
            # Firebase déjà initialisé
            if "already exists" in str(e):
                self.initialized = True
                logger.info("Firebase Admin SDK déjà initialisé")
                return True
            else:
                logger.error(f"Erreur Firebase: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation Firebase: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Vérifie si Firebase est initialisé"""
        return self.initialized


# Instance singleton
firebase_manager = FirebaseManager()


def initialize_firebase() -> bool:
    """Fonction helper pour initialiser Firebase"""
    return firebase_manager.initialize_firebase()


def is_firebase_initialized() -> bool:
    """Fonction helper pour vérifier l'état de Firebase"""
    return firebase_manager.is_initialized()