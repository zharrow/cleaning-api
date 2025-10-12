"""
Suppliers Router - HACCP Module
Manage food suppliers with HACCP certification tracking
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.haccp_models import Supplier
from api.schemas.haccp_schemas import SupplierCreate, SupplierUpdate, SupplierResponse

router = APIRouter()


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create a new supplier"""
    db_supplier = Supplier(
        enterprise_id=current_admin.enterprise.id,
        **supplier.dict()
    )
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.get("", response_model=List[SupplierResponse])
async def get_suppliers(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all suppliers for the current enterprise"""
    return db.query(Supplier).filter(Supplier.enterprise_id == current_admin.enterprise.id).order_by(Supplier.name).all()


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific supplier by ID"""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == current_admin.enterprise.id
    ).first()

    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update a supplier"""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == current_admin.enterprise.id
    ).first()

    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(supplier, key, value)

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete a supplier (hard delete)"""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == current_admin.enterprise.id
    ).first()

    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    db.delete(supplier)
    db.commit()
    return None
