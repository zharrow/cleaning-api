"""
Router for Developer management
Developers are super admins with analytics-only view
Only developers can create other developers and admins
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.core.database import get_db
from api.models.user import Developer
from api.schemas.user_schemas import DeveloperCreate, DeveloperResponse

router = APIRouter(prefix="/developers", tags=["Developers"])


@router.post("", response_model=DeveloperResponse, status_code=status.HTTP_201_CREATED)
async def create_developer(
    developer: DeveloperCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new Developer account
    NOTE: This should be protected by Firebase Auth verification
    """
    # Check if email already exists
    existing = db.query(Developer).filter(Developer.email == developer.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Developer with this email already exists"
        )

    # Check if firebase_uid already exists
    existing_uid = db.query(Developer).filter(Developer.firebase_uid == developer.firebase_uid).first()
    if existing_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Developer with this Firebase UID already exists"
        )

    # Create developer
    db_developer = Developer(**developer.dict())
    db.add(db_developer)
    db.commit()
    db.refresh(db_developer)

    return db_developer


@router.get("", response_model=List[DeveloperResponse])
async def list_developers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all developers
    NOTE: Should be protected - developers only
    """
    developers = db.query(Developer).offset(skip).limit(limit).all()
    return developers


@router.get("/{developer_id}", response_model=DeveloperResponse)
async def get_developer(
    developer_id: str,
    db: Session = Depends(get_db)
):
    """
    Get developer by ID
    NOTE: Should be protected - developers only
    """
    developer = db.query(Developer).filter(Developer.id == developer_id).first()
    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found"
        )
    return developer


@router.delete("/{developer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_developer(
    developer_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a developer
    NOTE: Should be protected - developers only
    WARNING: This will cascade delete all admins created by this developer
    """
    developer = db.query(Developer).filter(Developer.id == developer_id).first()
    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found"
        )

    db.delete(developer)
    db.commit()
    return None
