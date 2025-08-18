# api/core/auth_dependencies.py
from typing import List
from fastapi import Depends, HTTPException, status
from api.models.user import User, UserRole
from api.core.security import get_current_user

class RequireRole:
    """
    Dependency pour vérifier le rôle de l'utilisateur
    Simplifié : GERANTE a accès à tout par défaut
    """
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        # Vérifier si l'utilisateur est actif
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte utilisateur désactivé"
            )
        
        # GERANTE et ADMIN ont accès à tout
        if current_user.role in [UserRole.ADMIN, UserRole.GERANTE]:
            return current_user
            
        # Sinon vérifier les rôles spécifiques
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle insuffisant. Rôle actuel: {current_user.role.value}"
            )
        return current_user

# ===== HELPERS POUR LES PERMISSIONS =====

def require_management_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur peut gérer l'application
    GERANTE et ADMIN autorisés
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé"
        )
    
    if not current_user.can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seuls les gérants peuvent accéder à cette ressource."
        )
    return current_user

def require_admin_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur est administrateur
    Seul ADMIN autorisé
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seuls les administrateurs peuvent accéder à cette ressource."
        )
    return current_user

# ===== ALIASES POUR LA COMPATIBILITÉ =====

# La plupart des endpoints utiliseront ceci
require_manager = require_management_access
require_gerante = require_management_access

# Pour les cas spéciaux
require_admin = require_admin_access

# Instances pour usage direct
require_any_role = RequireRole([UserRole.ADMIN, UserRole.GERANTE, UserRole.PERFORMER])
require_active_user = RequireRole([UserRole.ADMIN, UserRole.GERANTE])  # Par défaut