from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.task import TaskTemplate, AssignedTask
from api.schemas.task import TaskTemplateCreate, TaskTemplateResponse, AssignedTaskCreate, AssignedTaskResponse

router = APIRouter()
assigned_router = APIRouter()

# Task Templates
@router.post("", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_task_template(
    task: TaskTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mapper les champs frontend vers les champs du modèle
    task_data = task.model_dump()
    task_data['title'] = task_data.pop('name')  # Mapper name -> title
    db_task = TaskTemplate(**task_data)
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

@router.put("/{task_template_id}", response_model=TaskTemplateResponse, dependencies=[Depends(require_manager)])
async def update_task_template(
    task_template_id: str,
    payload: TaskTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task: Optional[TaskTemplate] = db.query(TaskTemplate).filter(TaskTemplate.id == task_template_id, TaskTemplate.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modèle de tâche introuvable")
    for k, v in payload.model_dump().items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_template_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
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
@assigned_router.post("", response_model=AssignedTaskResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_assigned_task(
    task: AssignedTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Convertir les strings en UUID et préparer les données
    task_data = task.model_dump()
    
    # Convertir les IDs string en UUID
    import uuid
    task_data['task_template_id'] = uuid.UUID(task_data['task_template_id'])
    task_data['room_id'] = uuid.UUID(task_data['room_id'])
    
    # Gérer le cas où default_performer_id est vide ou null
    if task_data.get('default_performer_id') and task_data['default_performer_id'].strip():
        task_data['default_performer_id'] = uuid.UUID(task_data['default_performer_id'])
    else:
        task_data['default_performer_id'] = None
    
    # Mapper frequency_days vers frequency pour le modèle
    if 'frequency_days' in task_data:
        task_data['frequency'] = task_data.pop('frequency_days')
    
    # Supprimer times_per_day car il fait partie de frequency
    task_data.pop('times_per_day', None)
    
    print(f"🔄 Création tâche assignée avec données: {task_data}")
    
    # Vérifier que les entités existent
    task_template = db.query(TaskTemplate).filter(TaskTemplate.id == task_data['task_template_id']).first()
    if not task_template:
        raise HTTPException(status_code=404, detail="Modèle de tâche introuvable")
    
    from api.models.room import Room
    room = db.query(Room).filter(Room.id == task_data['room_id']).first()
    if not room:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    
    # TODO: Vérifier que l'exécutant existe une fois qu'on aura une interface pour les créer
    # from api.models.performer import Performer  
    # performer = db.query(Performer).filter(Performer.id == task_data['default_performer_id']).first()
    # if not performer:
    #     raise HTTPException(status_code=404, detail="Exécutant introuvable")
    
    db_task = AssignedTask(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return AssignedTaskResponse.from_orm_model(db_task)

@assigned_router.get("", response_model=List[AssignedTaskResponse])
async def get_assigned_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    tasks = db.query(AssignedTask).options(
        joinedload(AssignedTask.task_template),
        joinedload(AssignedTask.room),
        joinedload(AssignedTask.default_performer)
    ).filter(AssignedTask.is_active == True).all()
    
    return [AssignedTaskResponse.from_orm_model(task) for task in tasks]

@assigned_router.put("/{assigned_task_id}", response_model=AssignedTaskResponse, dependencies=[Depends(require_manager)])
async def update_assigned_task(
    assigned_task_id: str,
    payload: AssignedTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task: Optional[AssignedTask] = db.query(AssignedTask).filter(AssignedTask.id == assigned_task_id, AssignedTask.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche assignée introuvable")
    for k, v in payload.model_dump().items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return AssignedTaskResponse.from_orm_model(task)

@assigned_router.delete("/{assigned_task_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
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
