from typing import Optional
from fastapi import Depends, HTTPException, status
from api.models.user import User, UserRole
from api.core.security import get_current_user

class RequireRole:
    """Dependency pour vérifier le rôle de l'utilisateur"""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle insuffisant. Rôles autorisés: {[r.value for r in self.allowed_roles]}"
            )
        return current_user

# Helper pour le rôle courant utilisé
require_gerante = RequireRole([UserRole.GERANTE])