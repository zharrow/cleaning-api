import time
import uuid
import json
from datetime import datetime
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from api.core.config import settings

# Configuration du logger
logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ajoute un ID unique à chaque requête pour le suivi"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class TimingMiddleware(BaseHTTPMiddleware):
    """Mesure le temps de traitement des requêtes"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log les requêtes lentes (>1s)
        if process_time > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging structuré des requêtes HTTP"""
    
    async def dispatch(self, request: Request, call_next):
        # Récupérer l'ID de requête
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log de la requête entrante
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )
        
        # Traiter la requête
        response = await call_next(request)
        
        # Log de la réponse
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "method": request.method,
                "path": request.url.path,
            }
        )
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Gestion centralisée des erreurs"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            logger.error(f"ValueError: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "message": str(e),
                    "request_id": getattr(request.state, "request_id", "unknown")
                }
            )
        except PermissionError as e:
            logger.error(f"PermissionError: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": "Vous n'avez pas les permissions nécessaires",
                    "request_id": getattr(request.state, "request_id", "unknown")
                }
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "Une erreur inattendue s'est produite" if settings.environment == "production" else str(e),
                    "request_id": getattr(request.state, "request_id", "unknown")
                }
            )

class RateLimitMiddleware:
    """Limitation du nombre de requêtes par IP"""
    
    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extraire l'IP client
        headers = dict(scope.get("headers", []))
        client_host = None
        
        # Vérifier X-Forwarded-For pour les proxies
        forwarded = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            client_host = forwarded.split(",")[0].strip()
        else:
            client = scope.get("client")
            if client:
                client_host = client[0]
        
        if not client_host:
            await self.app(scope, receive, send)
            return
        
        # Vérifier le rate limit
        now = time.time()
        
        # Nettoyer les anciennes entrées
        self.clients = {
            ip: timestamps 
            for ip, timestamps in self.clients.items() 
            if any(ts > now - self.period for ts in timestamps)
        }
        
        # Vérifier les requêtes de ce client
        if client_host in self.clients:
            recent_calls = [ts for ts in self.clients[client_host] if ts > now - self.period]
            if len(recent_calls) >= self.calls:
                response = Response(
                    content=json.dumps({
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {self.calls} requêtes par {self.period} secondes"
                    }),
                    status_code=429,
                    media_type="application/json"
                )
                await response(scope, receive, send)
                return
            self.clients[client_host] = recent_calls + [now]
        else:
            self.clients[client_host] = [now]
        
        await self.app(scope, receive, send)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Ajoute des headers de sécurité aux réponses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers de sécurité
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy adaptée selon la route
        path = request.url.path
        
        if path.startswith("/docs") or path.startswith("/redoc") or path == "/openapi.json":
            # CSP permissive pour la documentation (ReDoc utilise des Workers)
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: blob: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
                "worker-src 'self' blob:; "
                "connect-src 'self'"
            )
        elif settings.environment == "development":
            # CSP plus permissive en développement
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "worker-src 'self' blob:"
            )
        else:
            # CSP stricte en production
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        
        return response

class DatabaseTransactionMiddleware(BaseHTTPMiddleware):
    """Gère les transactions de base de données automatiquement"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip pour les routes qui n'utilisent pas la DB
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        response = await call_next(request)
        
        # Si erreur 5xx, on pourrait rollback ici si nécessaire
        if response.status_code >= 500:
            logger.error(f"Server error on {request.method} {request.url.path}")
        
        return response