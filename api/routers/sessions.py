import uuid
from typing import List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.session import CleaningSession, SessionStatus
from api.schemas.session import CleaningSessionResponse
from api.utils.pagination import PaginationParams, paginate, create_paginated_response, PaginatedResponse
from api.utils.filters import DateRangeFilter, StatusFilter
from api.core.cache import cached

router = APIRouter()

@router.get("", response_model=List[CleaningSessionResponse])
async def get_sessions(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(CleaningSession).order_by(desc(CleaningSession.date)).limit(limit).all()

@router.get("/{session_id}", response_model=CleaningSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return session

@router.get("/today", response_model=CleaningSessionResponse)
async def get_today_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    session = db.query(CleaningSession).filter(CleaningSession.date == today).first()
    
    if not session:
        session = CleaningSession(date=today)
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session

@router.patch("/{session_id}/status")
async def update_session_status(
    session_id: uuid.UUID,
    status: SessionStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session.status = status
    session.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Statut mis à jour"}

@router.get("", response_model=PaginatedResponse[CleaningSessionResponse])
@cached(expire=60, key_prefix="sessions")
async def get_sessions(
    pagination: PaginationParams = Depends(),
    date_filter: DateRangeFilter = Depends(),
    status_filter: StatusFilter = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste paginée des sessions avec filtres
    
    - **page**: Numéro de page (défaut: 1)
    - **size**: Nombre d'éléments par page (défaut: 20, max: 100)
    - **start_date**: Filtrer à partir de cette date
    - **end_date**: Filtrer jusqu'à cette date
    - **status**: Filtrer par statut(s)
    """
    query = db.query(CleaningSession)
    
    # Appliquer les filtres
    query = date_filter.apply(query, CleaningSession.date)
    query = status_filter.apply(query, CleaningSession.status)
    
    # Ordonner
    query = query.order_by(desc(CleaningSession.date))
    
    # Paginer
    items, total = paginate(query, pagination)
    
    return create_paginated_response(
        items=items,
        total=total,
        params=pagination,
        response_model=CleaningSessionResponse
    )
