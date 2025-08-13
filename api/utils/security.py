# api/utils/security.py

"""
Utilitaires de sécurité pour l'API
"""

import hashlib
import hmac
import secrets
import string
from typing import Optional, Union
from datetime import datetime, timedelta
import re
from pathlib import Path
import mimetypes
import bleach
from fastapi import UploadFile, HTTPException, status

# Patterns de validation sécurisés
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
SQL_INJECTION_PATTERN = re.compile(r'(union|select|insert|update|delete|drop|create|alter|exec|script)', re.IGNORECASE)
XSS_PATTERN = re.compile(r'<script|javascript:|onerror=|onclick=|onload=', re.IGNORECASE)

# Types MIME autorisés pour les uploads
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp'],
    'image/gif': ['.gif']
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
}

def generate_secure_token(length: int = 32) -> str:
    """
    Génère un token sécurisé aléatoire
    
    Args:
        length: Longueur du token
        
    Returns:
        Token sécurisé
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_key() -> str:
    """
    Génère une clé API sécurisée
    
    Returns:
        Clé API au format sk_xxxxxx
    """
    return f"sk_{generate_secure_token(48)}"

def hash_string(data: str, salt: Optional[str] = None) -> str:
    """
    Hash une chaîne avec SHA256
    
    Args:
        data: Donnée à hasher
        salt: Sel optionnel
        
    Returns:
        Hash hexadécimal
    """
    if salt:
        data = f"{salt}{data}"
    return hashlib.sha256(data.encode()).hexdigest()

def verify_hash(data: str, hash_value: str, salt: Optional[str] = None) -> bool:
    """
    Vérifie qu'une donnée correspond à un hash
    
    Args:
        data: Donnée à vérifier
        hash_value: Hash à comparer
        salt: Sel optionnel
        
    Returns:
        True si les hash correspondent
    """
    return hash_string(data, salt) == hash_value

def create_signature(data: str, secret: str) -> str:
    """
    Crée une signature HMAC pour une donnée
    
    Args:
        data: Donnée à signer
        secret: Clé secrète
        
    Returns:
        Signature hexadécimale
    """
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_signature(data: str, signature: str, secret: str) -> bool:
    """
    Vérifie une signature HMAC
    
    Args:
        data: Donnée signée
        signature: Signature à vérifier
        secret: Clé secrète
        
    Returns:
        True si la signature est valide
    """
    expected_signature = create_signature(data, secret)
    return hmac.compare_digest(expected_signature, signature)

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre sûr
    
    Args:
        filename: Nom de fichier original
        
    Returns:
        Nom de fichier sécurisé
    """
    # Garder seulement l'extension et le nom de base
    name = Path(filename).stem
    ext = Path(filename).suffix.lower()
    
    # Remplacer les caractères non sûrs
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    
    # Limiter la longueur
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    
    # Ajouter un timestamp pour l'unicité
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{safe_name}_{timestamp}{ext}"

def validate_file_type(file: UploadFile, allowed_types: dict) -> bool:
    """
    Valide le type MIME d'un fichier
    
    Args:
        file: Fichier uploadé
        allowed_types: Types MIME autorisés
        
    Returns:
        True si le type est autorisé
    """
    if not file.content_type:
        return False
    
    # Vérifier le type MIME
    if file.content_type not in allowed_types:
        return False
    
    # Vérifier l'extension
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = allowed_types.get(file.content_type, [])
    
    return file_ext in allowed_extensions

def validate_image_file(file: UploadFile) -> None:
    """
    Valide qu'un fichier est une image autorisée
    
    Args:
        file: Fichier uploadé
        
    Raises:
        HTTPException: Si le fichier n'est pas valide
    """
    if not validate_file_type(file, ALLOWED_IMAGE_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non autorisé. Types acceptés: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"
        )

def validate_file_size(file: UploadFile, max_size_mb: int = 10) -> None:
    """
    Valide la taille d'un fichier
    
    Args:
        file: Fichier uploadé
        max_size_mb: Taille maximale en MB
        
    Raises:
        HTTPException: Si le fichier est trop gros
    """
    # Lire le fichier pour obtenir sa taille
    file.file.seek(0, 2)  # Aller à la fin
    file_size = file.file.tell()
    file.file.seek(0)  # Retourner au début
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux. Taille maximale: {max_size_mb}MB"
        )

def sanitize_html(html: str, allowed_tags: Optional[list] = None) -> str:
    """
    Nettoie du HTML pour éviter les attaques XSS
    
    Args:
        html: HTML à nettoyer
        allowed_tags: Tags autorisés (par défaut: basiques)
        
    Returns:
        HTML nettoyé
    """
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
    
    return bleach.clean(
        html,
        tags=allowed_tags,
        strip=True
    )

def validate_email(email: str) -> bool:
    """
    Valide une adresse email
    
    Args:
        email: Email à valider
        
    Returns:
        True si l'email est valide
    """
    if not email or len(email) > 254:
        return False
    
    return bool(EMAIL_PATTERN.match(email))

def check_sql_injection(text: str) -> bool:
    """
    Vérifie si un texte contient des patterns d'injection SQL
    
    Args:
        text: Texte à vérifier
        
    Returns:
        True si suspect
    """
    return bool(SQL_INJECTION_PATTERN.search(text))

def check_xss_attack(text: str) -> bool:
    """
    Vérifie si un texte contient des patterns XSS
    
    Args:
        text: Texte à vérifier
        
    Returns:
        True si suspect
    """
    return bool(XSS_PATTERN.search(text))

def validate_input(text: str, max_length: int = 1000) -> str:
    """
    Valide et nettoie une entrée utilisateur
    
    Args:
        text: Texte à valider
        max_length: Longueur maximale
        
    Returns:
        Texte validé
        
    Raises:
        HTTPException: Si le texte est suspect
    """
    if not text:
        return ""
    
    # Vérifier la longueur
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Texte trop long (max: {max_length} caractères)"
        )
    
    # Vérifier les injections SQL
    if check_sql_injection(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contenu suspect détecté"
        )
    
    # Vérifier les attaques XSS
    if check_xss_attack(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contenu HTML non autorisé"
        )
    
    # Nettoyer les espaces
    return text.strip()

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Masque des données sensibles (tokens, clés API, etc)
    
    Args:
        data: Donnée à masquer
        visible_chars: Nombre de caractères visibles au début/fin
        
    Returns:
        Donnée masquée
    """
    if len(data) <= visible_chars * 2:
        return "*" * len(data)
    
    return f"{data[:visible_chars]}{'*' * (len(data) - visible_chars * 2)}{data[-visible_chars:]}"

def generate_otp(length: int = 6) -> str:
    """
    Génère un code OTP numérique
    
    Args:
        length: Longueur du code
        
    Returns:
        Code OTP
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def is_strong_password(password: str) -> tuple[bool, list[str]]:
    """
    Vérifie la force d'un mot de passe
    
    Args:
        password: Mot de passe à vérifier
        
    Returns:
        (is_strong, list_of_issues)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Au moins 8 caractères requis")
    
    if not re.search(r'[A-Z]', password):
        issues.append("Au moins une majuscule requise")
    
    if not re.search(r'[a-z]', password):
        issues.append("Au moins une minuscule requise")
    
    if not re.search(r'\d', password):
        issues.append("Au moins un chiffre requis")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Au moins un caractère spécial requis")
    
    return len(issues) == 0, issues

def rate_limit_key(user_id: str, action: str) -> str:
    """
    Génère une clé pour le rate limiting
    
    Args:
        user_id: ID de l'utilisateur
        action: Action effectuée
        
    Returns:
        Clé de rate limiting
    """
    return f"rate_limit:{action}:{user_id}"

def get_client_ip(request) -> str:
    """
    Récupère l'IP réelle du client (gère les proxies)
    
    Args:
        request: Requête FastAPI
        
    Returns:
        Adresse IP
    """
    # Vérifier les headers de proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback sur l'IP de la connexion
    if request.client:
        return request.client.host
    
    return "unknown"

class SecurityHeaders:
    """Headers de sécurité recommandés"""
    
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": "default-src 'self'"
    }
    
    @classmethod
    def get_headers(cls, custom_csp: Optional[str] = None) -> dict:
        """
        Retourne les headers de sécurité
        
        Args:
            custom_csp: CSP personnalisé
            
        Returns:
            Dict des headers
        """
        headers = cls.HEADERS.copy()
        if custom_csp:
            headers["Content-Security-Policy"] = custom_csp
        return headers

# Constantes de sécurité
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)
SESSION_TIMEOUT = timedelta(hours=24)
PASSWORD_RESET_TIMEOUT = timedelta(hours=1)
OTP_VALIDITY = timedelta(minutes=5)

# Messages d'erreur génériques (pour éviter les fuites d'information)
GENERIC_ERROR_MESSAGE = "Une erreur s'est produite. Veuillez réessayer."
INVALID_CREDENTIALS_MESSAGE = "Identifiants invalides"
ACCOUNT_LOCKED_MESSAGE = "Compte temporairement verrouillé"