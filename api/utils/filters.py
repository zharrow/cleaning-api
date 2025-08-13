"""
Système de filtres réutilisables
"""

from typing import Optional, List
from datetime import date, datetime
from fastapi import Query
from sqlalchemy.orm import Query as SQLQuery
from sqlalchemy import and_, or_

class DateRangeFilter:
    """Filtre par plage de dates"""
    def __init__(
        self,
        start_date: Optional[date] = Query(None, description="Date de début"),
        end_date: Optional[date] = Query(None, description="Date de fin")
    ):
        self.start_date = start_date
        self.end_date = end_date
    
    def apply(self, query: SQLQuery, field) -> SQLQuery:
        if self.start_date:
            query = query.filter(field >= self.start_date)
        if self.end_date:
            query = query.filter(field <= self.end_date)
        return query

class SearchFilter:
    """Filtre de recherche textuelle"""
    def __init__(
        self,
        q: Optional[str] = Query(None, description="Terme de recherche")
    ):
        self.q = q
    
    def apply(self, query: SQLQuery, *fields) -> SQLQuery:
        if not self.q:
            return query
        
        search_term = f"%{self.q}%"
        conditions = [field.ilike(search_term) for field in fields]
        return query.filter(or_(*conditions))

class StatusFilter:
    """Filtre par statut"""
    def __init__(
        self,
        status: Optional[List[str]] = Query(None, description="Filtrer par statut")
    ):
        self.status = status
    
    def apply(self, query: SQLQuery, field) -> SQLQuery:
        if self.status:
            return query.filter(field.in_(self.status))
        return query

# Exemple d'utilisation mise à jour des routers