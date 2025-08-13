# api/core/csp_config.py

"""
Configuration flexible pour Content Security Policy
"""

from typing import Dict, Optional
from api.core.config import settings

class CSPConfig:
    """Configuration centralisée pour les CSP"""
    
    # CSP pour la documentation (ReDoc, Swagger)
    DOCUMENTATION_CSP = {
        "default-src": "'self' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com",
        "script-src": "'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net https://unpkg.com",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://unpkg.com",
        "font-src": "'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
        "img-src": "'self' data: blob: https: http:",
        "worker-src": "'self' blob:",
        "child-src": "'self' blob:",
        "connect-src": "'self' https://cdn.jsdelivr.net",
        "frame-ancestors": "'none'",
        "object-src": "'none'",
        "base-uri": "'self'"
    }
    
    # CSP pour le développement
    DEVELOPMENT_CSP = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' 'unsafe-eval' blob:",
        "style-src": "'self' 'unsafe-inline'",
        "img-src": "'self' data: blob: https: http:",
        "font-src": "'self' data:",
        "connect-src": "'self' ws: wss: http: https:",
        "worker-src": "'self' blob:",
        "child-src": "'self' blob:",
        "frame-ancestors": "'none'",
        "object-src": "'none'",
        "base-uri": "'self'"
    }
    
    # CSP pour la production
    PRODUCTION_CSP = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self' 'unsafe-inline'",  # unsafe-inline souvent nécessaire pour les styles
        "img-src": "'self' data: https:",
        "font-src": "'self'",
        "connect-src": "'self' https:",
        "frame-ancestors": "'none'",
        "object-src": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
        "upgrade-insecure-requests": ""
    }
    
    @staticmethod
    def build_csp_header(csp_dict: Dict[str, str]) -> str:
        """
        Construit un header CSP à partir d'un dictionnaire
        
        Args:
            csp_dict: Dictionnaire des directives CSP
            
        Returns:
            Header CSP formaté
        """
        directives = []
        for directive, value in csp_dict.items():
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
        return "; ".join(directives)
    
    @classmethod
    def get_csp_for_path(cls, path: str) -> str:
        """
        Retourne la CSP appropriée selon le chemin
        
        Args:
            path: Chemin de la requête
            
        Returns:
            Header CSP
        """
        # Chemins de documentation
        doc_paths = ["/docs", "/redoc", "/openapi.json"]
        if any(path.startswith(p) for p in doc_paths):
            return cls.build_csp_header(cls.DOCUMENTATION_CSP)
        
        # Environnement de développement
        if settings.environment == "development":
            return cls.build_csp_header(cls.DEVELOPMENT_CSP)
        
        # Production par défaut
        return cls.build_csp_header(cls.PRODUCTION_CSP)

# Middleware amélioré avec configuration flexible
class FlexibleSecurityHeadersMiddleware:
    """Middleware de sécurité avec CSP flexible"""
    
    def __init__(self, app, disable_csp: bool = False, custom_headers: Optional[Dict[str, str]] = None):
        self.app = app
        self.disable_csp = disable_csp
        self.custom_headers = custom_headers or {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Headers de sécurité de base
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()"
                }
                
                # HSTS seulement en production
                if settings.environment == "production":
                    security_headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                
                # CSP si non désactivée
                if not self.disable_csp:
                    path = scope.get("path", "/")
                    csp = CSPConfig.get_csp_for_path(path)
                    security_headers[b"content-security-policy"] = csp.encode()
                
                # Ajouter les headers personnalisés
                for name, value in self.custom_headers.items():
                    security_headers[name.encode()] = value.encode()
                
                # Mettre à jour les headers
                for name, value in security_headers.items():
                    headers[name] = value
                
                # Reconstruire la liste des headers
                message["headers"] = [(k, v) for k, v in headers.items()]
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)