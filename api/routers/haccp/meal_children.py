"""Meal Children Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.haccp_models import MealChildren, Meal, Child
from api.schemas.haccp_schemas import MealChildrenCreate, MealChildrenUpdate, MealChildrenResponse

router = APIRouter()

@router.post("", response_model=MealChildrenResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_child(mc: MealChildrenCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    # Verify meal belongs to enterprise
    meal = db.query(Meal).filter(
        Meal.id == mc.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()

    # Verify child belongs to enterprise
    child = db.query(Child).filter(
        Child.id == mc.child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not meal or not child:
        raise HTTPException(status_code=404, detail="Meal or child not found or access denied")

    db_mc = MealChildren(**mc.dict())
    db.add(db_mc)
    db.commit()
    db.refresh(db_mc)
    return db_mc

@router.get("", response_model=List[MealChildrenResponse])
async def get_meal_children(meal_id: str = None, child_id: str = None, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    # Get meal_children through meals and children owned by admin's enterprise
    query = db.query(MealChildren).join(Meal).join(Child).filter(
        Meal.enterprise_id == current_admin.enterprise.id,
        Child.enterprise_id == current_admin.enterprise.id
    )
    if meal_id:
        query = query.filter(MealChildren.meal_id == meal_id)
    if child_id:
        query = query.filter(MealChildren.child_id == child_id)
    return query.all()

@router.get("/{mc_id}", response_model=MealChildrenResponse)
async def get_meal_child(mc_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    mc = db.query(MealChildren).filter(MealChildren.id == mc_id).first()
    if not mc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal-child association not found")

    # Verify meal belongs to enterprise
    meal = db.query(Meal).filter(
        Meal.id == mc.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()

    # Verify child belongs to enterprise
    child = db.query(Child).filter(
        Child.id == mc.child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not meal or not child:
        raise HTTPException(status_code=404, detail="Meal or child not found or access denied")

    return mc

@router.put("/{mc_id}", response_model=MealChildrenResponse)
async def update_meal_child(mc_id: str, payload: MealChildrenUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    mc = db.query(MealChildren).filter(MealChildren.id == mc_id).first()
    if not mc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal-child association not found")

    # Verify meal belongs to enterprise
    meal = db.query(Meal).filter(
        Meal.id == mc.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()

    # Verify child belongs to enterprise
    child = db.query(Child).filter(
        Child.id == mc.child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not meal or not child:
        raise HTTPException(status_code=404, detail="Meal or child not found or access denied")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(mc, key, value)
    db.commit()
    db.refresh(mc)
    return mc

@router.delete("/{mc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_child(mc_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    mc = db.query(MealChildren).filter(MealChildren.id == mc_id).first()
    if not mc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal-child association not found")

    # Verify meal belongs to enterprise
    meal = db.query(Meal).filter(
        Meal.id == mc.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()

    # Verify child belongs to enterprise
    child = db.query(Child).filter(
        Child.id == mc.child_id,
        Child.enterprise_id == current_admin.enterprise.id
    ).first()

    if not meal or not child:
        raise HTTPException(status_code=404, detail="Meal or child not found or access denied")

    db.delete(mc)
    db.commit()
    return None
