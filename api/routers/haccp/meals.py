"""Meals Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.enterprise import Enterprise
from api.models.haccp_models import Meal
from api.schemas.haccp_schemas import MealCreate, MealUpdate, MealResponse

router = APIRouter()

@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_meal(meal: MealCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    db_meal = Meal(enterprise_id=enterprise.id, **meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@router.get("", response_model=List[MealResponse])
async def get_meals(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return db.query(Meal).filter(Meal.enterprise_id == enterprise.id).order_by(Meal.date.desc()).all()

@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(meal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.enterprise_id == enterprise.id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal

@router.put("/{meal_id}", response_model=MealResponse, dependencies=[Depends(require_manager)])
async def update_meal(meal_id: str, payload: MealUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.enterprise_id == enterprise.id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(meal, key, value)
    db.commit()
    db.refresh(meal)
    return meal

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_meal(meal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.enterprise_id == enterprise.id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    db.delete(meal)
    db.commit()
    return None
