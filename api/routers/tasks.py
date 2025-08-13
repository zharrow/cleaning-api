from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_gerante
from api.models.user import User
from api.models.task import TaskTemplate, AssignedTask
from api.schemas.task import TaskTemplateCreate, TaskTemplateResponse, AssignedTaskCreate, AssignedTaskResponse

router = APIRouter()
assigned_router = APIRouter()

# Task Templates
@router.post("", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_gerante)])
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

@router.put("/{task_template_id}", response_model=TaskTemplateResponse, dependencies=[Depends(require_gerante)])
async def update_task_template(
    task_template_id: str,
    payload: TaskTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task: Optional[TaskTemplate] = db.query(TaskTemplate).filter(TaskTemplate.id == task_template_id, TaskTemplate.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modèle de tâche introuvable")
    for k, v in payload.dict().items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_template_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_gerante)])
async def delete_task_template(
    task_template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task: Optional[TaskTemplate] = db.query(TaskTemplate).filter(TaskTemplate.id == task_template_id, TaskTemplate.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modèle de tâche introuvable")
    task.is_active = False
    db.commit()
    return None

# Assigned Tasks
@assigned_router.post("", response_model=AssignedTaskResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_gerante)])
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

@assigned_router.put("/{assigned_task_id}", response_model=AssignedTaskResponse, dependencies=[Depends(require_gerante)])
async def update_assigned_task(
    assigned_task_id: str,
    payload: AssignedTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task: Optional[AssignedTask] = db.query(AssignedTask).filter(AssignedTask.id == assigned_task_id, AssignedTask.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche assignée introuvable")
    for k, v in payload.dict().items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task

@assigned_router.delete("/{assigned_task_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_gerante)])
async def delete_assigned_task(
    assigned_task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task: Optional[AssignedTask] = db.query(AssignedTask).filter(AssignedTask.id == assigned_task_id, AssignedTask.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche assignée introuvable")
    task.is_active = False
    db.commit()
    return None
