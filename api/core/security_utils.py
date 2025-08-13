import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from api.core.config import settings

# Configuration du hashing de mots de passe (si besoin futur)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_token(length: int = 32) -> str:
    """Génère un token aléatoire sécurisé"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_key() -> str:
    """Génère une clé API"""
    return f"sk_{generate_token(48)}"

def create_jwt_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    secret_key: str = None
) -> str:
    """
    Crée un token JWT (pour usage futur si migration depuis Firebase)
    """
    if secret_key is None:
        secret_key = settings.secret_key
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

def verify_jwt_token(token: str, secret_key: str = None) -> Optional[dict]:
    """
    Vérifie un token JWT (pour usage futur)
    """
    if secret_key is None:
        secret_key = settings.secret_key
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def hash_password(password: str) -> str:
    """Hash un mot de passe"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return pwd_context.verify(plain_password, hashed_password)