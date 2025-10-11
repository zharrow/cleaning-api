"""Non-Compliances Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.enterprise import Enterprise
from api.models.haccp_models import NonCompliance
from api.schemas.haccp_schemas import NonComplianceCreate, NonComplianceUpdate, NonComplianceResponse

router = APIRouter()

@router.post("", response_model=NonComplianceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_non_compliance(nc: NonComplianceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    db_nc = NonCompliance(enterprise_id=enterprise.id, **nc.dict())
    db.add(db_nc)
    db.commit()
    db.refresh(db_nc)
    return db_nc

@router.get("", response_model=List[NonComplianceResponse])
async def get_non_compliances(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return db.query(NonCompliance).filter(NonCompliance.enterprise_id == enterprise.id).order_by(NonCompliance.report_date.desc()).all()

@router.get("/{nc_id}", response_model=NonComplianceResponse)
async def get_non_compliance(nc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    nc = db.query(NonCompliance).filter(NonCompliance.id == nc_id, NonCompliance.enterprise_id == enterprise.id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non-compliance not found")
    return nc

@router.put("/{nc_id}", response_model=NonComplianceResponse, dependencies=[Depends(require_manager)])
async def update_non_compliance(nc_id: str, payload: NonComplianceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    nc = db.query(NonCompliance).filter(NonCompliance.id == nc_id, NonCompliance.enterprise_id == enterprise.id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non-compliance not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(nc, key, value)
    db.commit()
    db.refresh(nc)
    return nc

@router.delete("/{nc_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_non_compliance(nc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    nc = db.query(NonCompliance).filter(NonCompliance.id == nc_id, NonCompliance.enterprise_id == enterprise.id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non-compliance not found")
    db.delete(nc)
    db.commit()
    return None
