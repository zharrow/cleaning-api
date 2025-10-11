"""Cleaning HACCP Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.enterprise import Enterprise
from api.models.haccp_models import CleaningHaccp
from api.schemas.haccp_schemas import CleaningHaccpCreate, CleaningHaccpUpdate, CleaningHaccpResponse

router = APIRouter()

@router.post("", response_model=CleaningHaccpResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_cleaning_haccp(cleaning: CleaningHaccpCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    db_cleaning = CleaningHaccp(enterprise_id=enterprise.id, **cleaning.dict())
    db.add(db_cleaning)
    db.commit()
    db.refresh(db_cleaning)
    return db_cleaning

@router.get("", response_model=List[CleaningHaccpResponse])
async def get_cleaning_haccp_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return db.query(CleaningHaccp).filter(CleaningHaccp.enterprise_id == enterprise.id).order_by(CleaningHaccp.cleaning_date.desc()).all()

@router.get("/{cleaning_id}", response_model=CleaningHaccpResponse)
async def get_cleaning_haccp(cleaning_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    cleaning = db.query(CleaningHaccp).filter(CleaningHaccp.id == cleaning_id, CleaningHaccp.enterprise_id == enterprise.id).first()
    if not cleaning:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cleaning HACCP record not found")
    return cleaning

@router.put("/{cleaning_id}", response_model=CleaningHaccpResponse, dependencies=[Depends(require_manager)])
async def update_cleaning_haccp(cleaning_id: str, payload: CleaningHaccpUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    cleaning = db.query(CleaningHaccp).filter(CleaningHaccp.id == cleaning_id, CleaningHaccp.enterprise_id == enterprise.id).first()
    if not cleaning:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cleaning HACCP record not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(cleaning, key, value)
    db.commit()
    db.refresh(cleaning)
    return cleaning

@router.delete("/{cleaning_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_cleaning_haccp(cleaning_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    cleaning = db.query(CleaningHaccp).filter(CleaningHaccp.id == cleaning_id, CleaningHaccp.enterprise_id == enterprise.id).first()
    if not cleaning:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cleaning HACCP record not found")
    db.delete(cleaning)
    db.commit()
    return None
