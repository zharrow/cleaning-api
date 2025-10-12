"""
Router for Admin management
Admins are daycare managers created by Developers
1 Admin = 1 Enterprise = 1 Daycare
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.core.database import get_db
from api.models.user import Admin, Developer
from api.models.enterprise import Enterprise
from api.schemas.user_schemas import AdminCreate, AdminUpdate, AdminResponse, EnterpriseCreate, EnterpriseResponse

router = APIRouter(prefix="/admins", tags=["Admins"])


@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin: AdminCreate,
    developer_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new Admin account
    NOTE: Should be called by Developers only via Firebase Auth
    """
    # Verify developer exists
    developer = db.query(Developer).filter(Developer.id == developer_id).first()
    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found"
        )

    # Check if email already exists
    existing = db.query(Admin).filter(Admin.email == admin.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )

    # Check if firebase_uid already exists
    existing_uid = db.query(Admin).filter(Admin.firebase_uid == admin.firebase_uid).first()
    if existing_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this Firebase UID already exists"
        )

    # Create admin
    db_admin = Admin(**admin.dict(), created_by_id=developer_id)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)

    return db_admin


@router.get("", response_model=List[AdminResponse])
async def list_admins(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all admins
    NOTE: Should be protected - developers only
    """
    admins = db.query(Admin).offset(skip).limit(limit).all()
    return admins


@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: str,
    db: Session = Depends(get_db)
):
    """
    Get admin by ID
    """
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin


@router.patch("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: str,
    admin_update: AdminUpdate,
    db: Session = Depends(get_db)
):
    """
    Update admin information
    """
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    # Update only provided fields
    update_data = admin_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(admin, key, value)

    db.commit()
    db.refresh(admin)
    return admin


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete an admin (soft delete by setting is_active=False)
    NOTE: Should be protected - developers only
    """
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    # Soft delete
    admin.is_active = False
    db.commit()
    return None


# ==================== ENTERPRISE MANAGEMENT ====================

@router.post("/{admin_id}/enterprise", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
async def create_enterprise_for_admin(
    admin_id: str,
    enterprise: EnterpriseCreate,
    db: Session = Depends(get_db)
):
    """
    Create an enterprise for an admin
    1 Admin can only have 1 Enterprise
    """
    # Verify admin exists
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    # Check if admin already has an enterprise
    existing = db.query(Enterprise).filter(Enterprise.admin_id == admin_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin already has an enterprise"
        )

    # Create enterprise
    db_enterprise = Enterprise(**enterprise.dict(), admin_id=admin_id)
    db.add(db_enterprise)
    db.commit()
    db.refresh(db_enterprise)

    return db_enterprise


@router.get("/{admin_id}/enterprise", response_model=EnterpriseResponse)
async def get_admin_enterprise(
    admin_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the enterprise for an admin
    """
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == admin_id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enterprise not found for this admin"
        )
    return enterprise
