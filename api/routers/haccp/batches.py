"""Batches Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.haccp_models import Batch, Product
from api.schemas.haccp_schemas import BatchCreate, BatchUpdate, BatchResponse

router = APIRouter()

@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(batch: BatchCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    # Verify product belongs to admin's enterprise
    product = db.query(Product).filter(
        Product.id == batch.product_id,
        Product.enterprise_id == current_admin.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")

    db_batch = Batch(**batch.dict())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

@router.get("", response_model=List[BatchResponse])
async def get_batches(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    # Get batches through products owned by admin's enterprise
    return db.query(Batch).join(Product).filter(Product.enterprise_id == current_admin.enterprise.id).all()

@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    # Verify product belongs to admin's enterprise
    product = db.query(Product).filter(
        Product.id == batch.product_id,
        Product.enterprise_id == current_admin.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")

    return batch

@router.put("/{batch_id}", response_model=BatchResponse)
async def update_batch(batch_id: str, payload: BatchUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    # Verify product belongs to admin's enterprise
    product = db.query(Product).filter(
        Product.id == batch.product_id,
        Product.enterprise_id == current_admin.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(batch, key, value)
    db.commit()
    db.refresh(batch)
    return batch

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(batch_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    # Verify product belongs to admin's enterprise
    product = db.query(Product).filter(
        Product.id == batch.product_id,
        Product.enterprise_id == current_admin.enterprise.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")

    db.delete(batch)
    db.commit()
    return None
