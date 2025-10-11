"""Batches Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.haccp_models import Batch
from api.schemas.haccp_schemas import BatchCreate, BatchUpdate, BatchResponse

router = APIRouter()

@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_batch(batch: BatchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_batch = Batch(**batch.dict())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

@router.get("", response_model=List[BatchResponse])
async def get_batches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Batch).all()

@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch

@router.put("/{batch_id}", response_model=BatchResponse, dependencies=[Depends(require_manager)])
async def update_batch(batch_id: str, payload: BatchUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(batch, key, value)
    db.commit()
    db.refresh(batch)
    return batch

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_batch(batch_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    db.delete(batch)
    db.commit()
    return None
