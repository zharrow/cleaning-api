"""Meal Children Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.haccp_models import MealChildren
from api.schemas.haccp_schemas import MealChildrenCreate, MealChildrenUpdate, MealChildrenResponse

router = APIRouter()

@router.post("", response_model=MealChildrenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_meal_child(mc: MealChildrenCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_mc = MealChildren(**mc.dict())
    db.add(db_mc)
    db.commit()
    db.refresh(db_mc)
    return db_mc

@router.get("", response_model=List[MealChildrenResponse])
async def get_meal_children(meal_id: str = None, child_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(MealChildren)
    if meal_id:
        query = query.filter(MealChildren.meal_id == meal_id)
    if child_id:
        query = query.filter(MealChildren.child_id == child_id)
    return query.all()

@router.get("/{mc_id}", response_model=MealChildrenResponse)
async def get_meal_child(mc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mc = db.query(MealChildren).filter(MealChildren.id == mc_id).first()
    if not mc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal-child association not found")
    return mc

@router.put("/{mc_id}", response_model=MealChildrenResponse, dependencies=[Depends(require_manager)])
async def update_meal_child(mc_id: str, payload: MealChildrenUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mc = db.query(MealChildren).filter(MealChildren.id == mc_id).first()
    if not mc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal-child association not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(mc, key, value)
    db.commit()
    db.refresh(mc)
    return mc

@router.delete("/{mc_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_meal_child(mc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mc = db.query(MealChildren).filter(MealChildren.id == mc_id).first()
    if not mc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal-child association not found")
    db.delete(mc)
    db.commit()
    return None
