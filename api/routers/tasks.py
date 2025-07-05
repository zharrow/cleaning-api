from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.task import TaskTemplate, AssignedTask
from api.schemas.task import TaskTemplateCreate, TaskTemplateResponse, AssignedTaskCreate, AssignedTaskResponse

router = APIRouter()
assigned_router = APIRouter()

# Task Templates
@router.post("", response_model=TaskTemplateResponse)
async def create_task_template(
    task: TaskTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_task = TaskTemplate(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("", response_model=List[TaskTemplateResponse])
async def get_task_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(TaskTemplate).filter(TaskTemplate.is_active == True).all()

# Assigned Tasks
@assigned_router.post("", response_model=AssignedTaskResponse)
async def create_assigned_task(
    task: AssignedTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_task = AssignedTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@assigned_router.get("", response_model=List[AssignedTaskResponse])
async def get_assigned_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AssignedTask).filter(AssignedTask.is_active == True).all()
