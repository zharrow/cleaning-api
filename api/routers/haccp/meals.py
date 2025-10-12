"""Meals Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.haccp_models import Meal
from api.schemas.haccp_schemas import MealCreate, MealUpdate, MealResponse

router = APIRouter()

@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(meal: MealCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    db_meal = Meal(enterprise_id=current_admin.enterprise.id, **meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@router.get("", response_model=List[MealResponse])
async def get_meals(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    return db.query(Meal).filter(Meal.enterprise_id == current_admin.enterprise.id).order_by(Meal.date.desc()).all()

@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(meal_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.enterprise_id == current_admin.enterprise.id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal

@router.put("/{meal_id}", response_model=MealResponse)
async def update_meal(meal_id: str, payload: MealUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.enterprise_id == current_admin.enterprise.id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(meal, key, value)
    db.commit()
    db.refresh(meal)
    return meal

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.enterprise_id == current_admin.enterprise.id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    db.delete(meal)
    db.commit()
    return None
