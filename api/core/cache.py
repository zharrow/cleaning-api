"""
Système de cache avec Redis pour améliorer les performances
"""

import json
import redis
from typing import Optional, Any
from datetime import timedelta
from functools import wraps
import logging
from api.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Gestionnaire de cache Redis"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self._client = None
    
    @property
    def client(self):
        """Lazy loading du client Redis"""
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                self._client.ping()
                logger.info("✅ Connexion Redis établie")
            except Exception as e:
                logger.warning(f"⚠️ Redis non disponible: {e}")
                self._client = None
        return self._client
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Erreur lecture cache: {e}")
        return None
    
    def set(self, key: str, value: Any, expire: int = 300):
        """Stocke une valeur dans le cache"""
        if not self.client:
            return
        
        try:
            self.client.set(
                key, 
                json.dumps(value, default=str), 
                ex=expire
            )
        except Exception as e:
            logger.error(f"Erreur écriture cache: {e}")
    
    def delete(self, key: str):
        """Supprime une clé du cache"""
        if not self.client:
            return
        
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Erreur suppression cache: {e}")
    
    def clear_pattern(self, pattern: str):
        """Supprime toutes les clés correspondant au pattern"""
        if not self.client:
            return
        
        try:
            for key in self.client.scan_iter(match=pattern):
                self.client.delete(key)
        except Exception as e:
            logger.error(f"Erreur suppression pattern cache: {e}")

# Instance globale
cache = RedisCache()

def cached(expire: int = 300, key_prefix: str = ""):
    """
    Décorateur pour mettre en cache les résultats de fonction
    
    Usage:
        @cached(expire=600, key_prefix="rooms")
        async def get_rooms():
            return db.query(Room).all()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Construire la clé de cache
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Vérifier le cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Exécuter la fonction
            result = await func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator