"""Temperatures Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.haccp_models import Temperature, Meal
from api.schemas.haccp_schemas import TemperatureCreate, TemperatureUpdate, TemperatureResponse

router = APIRouter()

@router.post("", response_model=TemperatureResponse, status_code=status.HTTP_201_CREATED)
async def create_temperature(temp: TemperatureCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    # Verify meal belongs to admin's enterprise
    meal = db.query(Meal).filter(
        Meal.id == temp.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found or access denied")

    db_temp = Temperature(**temp.dict())
    db.add(db_temp)
    db.commit()
    db.refresh(db_temp)
    return db_temp

@router.get("", response_model=List[TemperatureResponse])
async def get_temperatures(meal_id: str = None, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    # Get temperatures through meals owned by admin's enterprise
    query = db.query(Temperature).join(Meal).filter(Meal.enterprise_id == current_admin.enterprise.id)
    if meal_id:
        query = query.filter(Temperature.meal_id == meal_id)
    return query.order_by(Temperature.control_date.desc()).all()

@router.get("/{temp_id}", response_model=TemperatureResponse)
async def get_temperature(temp_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    temp = db.query(Temperature).filter(Temperature.id == temp_id).first()
    if not temp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Temperature record not found")

    # Verify meal belongs to admin's enterprise
    meal = db.query(Meal).filter(
        Meal.id == temp.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found or access denied")

    return temp

@router.put("/{temp_id}", response_model=TemperatureResponse)
async def update_temperature(temp_id: str, payload: TemperatureUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    temp = db.query(Temperature).filter(Temperature.id == temp_id).first()
    if not temp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Temperature record not found")

    # Verify meal belongs to admin's enterprise
    meal = db.query(Meal).filter(
        Meal.id == temp.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found or access denied")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(temp, key, value)
    db.commit()
    db.refresh(temp)
    return temp

@router.delete("/{temp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_temperature(temp_id: str, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    temp = db.query(Temperature).filter(Temperature.id == temp_id).first()
    if not temp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Temperature record not found")

    # Verify meal belongs to admin's enterprise
    meal = db.query(Meal).filter(
        Meal.id == temp.meal_id,
        Meal.enterprise_id == current_admin.enterprise.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found or access denied")

    db.delete(temp)
    db.commit()
    return None
