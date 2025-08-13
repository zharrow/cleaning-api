"""
Utilitaires pour la pagination
"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from fastapi import Query
from sqlalchemy.orm import Query as SQLQuery

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Paramètres de pagination"""
    page: int = Query(1, ge=1, description="Numéro de page")
    size: int = Query(20, ge=1, le=100, description="Taille de page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1

def paginate(query: SQLQuery, params: PaginationParams) -> tuple[List, int]:
    """
    Applique la pagination à une query SQLAlchemy
    
    Returns:
        tuple: (items, total)
    """
    total = query.count()
    items = query.offset(params.offset).limit(params.size).all()
    return items, total

def create_paginated_response(
    items: List[T],
    total: int,
    params: PaginationParams,
    response_model: type[T]
) -> PaginatedResponse[T]:
    """Crée une réponse paginée"""
    pages = (total + params.size - 1) // params.size
    
    return PaginatedResponse[response_model](
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages
    )