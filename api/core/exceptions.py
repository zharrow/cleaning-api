"""
Exceptions personnalisées pour l'API
"""

from fastapi import HTTPException, status

class BusinessException(HTTPException):
    """Exception métier de base"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(BusinessException):
    """Ressource non trouvée"""
    def __init__(self, resource: str, id: str):
        super().__init__(
            detail=f"{resource} avec l'ID {id} non trouvé(e)",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ConflictException(BusinessException):
    """Conflit avec l'état actuel"""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )

class ValidationException(BusinessException):
    """Erreur de validation métier"""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

class UnauthorizedException(BusinessException):
    """Non autorisé"""
    def __init__(self, detail: str = "Non autorisé"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class ForbiddenException(BusinessException):
    """Accès interdit"""
    def __init__(self, detail: str = "Accès interdit"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )
