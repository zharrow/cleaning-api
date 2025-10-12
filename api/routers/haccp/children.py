"""
Children Router - HACCP Module
Manage children enrolled in daycare with allergen tracking
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.haccp_models import Child
from api.schemas.haccp_schemas import ChildCreate, ChildUpdate, ChildResponse

router = APIRouter()


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create a new child in the daycare"""
    db_child = Child(
        enterprise_id=current_admin.enterprise.id,
        **child.dict()
    )
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    return db_child


@router.get("", response_model=List[ChildResponse])
async def get_children(
    is_active: Optional[bool] = None,
    section: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all children for the current enterprise"""
    query = db.query(Child).filter(Child.enterprise_id == current_admin.enterprise.id)

    if is_active is not None:
        query = query.filter(Child.is_active == is_active)

    if section:
        query = query.filter(Child.section == section)

    return query.order_by(Child.last_name, Child.first_name).all()


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific child by ID"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    return child


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: str,
    payload: ChildUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update a child's information"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    # Update only provided fields
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(child, key, value)

    db.commit()
    db.refresh(child)
    return child


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Soft delete a child (set is_active to False)"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    child.is_active = False
    db.commit()
    return None
