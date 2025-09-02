import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import logging

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.enterprise import Enterprise
from api.schemas.enterprise import (
    EnterpriseCreate, 
    EnterpriseUpdate, 
    EnterpriseResponse, 
    EnterpriseBasicInfo
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/me", response_model=EnterpriseResponse)
async def get_my_enterprise(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les informations de l'entreprise de l'utilisateur connecté
    """
    enterprise = db.query(Enterprise).filter(
        Enterprise.user_id == current_user.id
    ).first()
    
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune entreprise associée à cet utilisateur"
        )
    
    return enterprise

@router.get("/me/basic", response_model=EnterpriseBasicInfo)
async def get_my_enterprise_basic_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les informations de base de l'entreprise (nom, logo) pour le header
    """
    enterprise = db.query(Enterprise).filter(
        Enterprise.user_id == current_user.id
    ).first()
    
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune entreprise associée à cet utilisateur"
        )
    
    return EnterpriseBasicInfo(
        name=enterprise.name,
        logo_url=enterprise.logo_url
    )

@router.post("/", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
async def create_enterprise(
    enterprise_data: EnterpriseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle entreprise pour l'utilisateur connecté
    """
    # Vérifier qu'une entreprise n'existe pas déjà pour cet utilisateur
    existing_enterprise = db.query(Enterprise).filter(
        Enterprise.user_id == current_user.id
    ).first()
    
    if existing_enterprise:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Une entreprise est déjà associée à cet utilisateur"
        )
    
    try:
        # Créer l'entreprise
        enterprise = Enterprise(
            user_id=current_user.id,
            name=enterprise_data.name,
            logo_url=enterprise_data.logo_url,
            legal_form=enterprise_data.legal_form,
            siret=enterprise_data.siret
        )
        
        db.add(enterprise)
        db.commit()
        db.refresh(enterprise)
        
        logger.info(f"Entreprise créée avec succès: {enterprise.name} par utilisateur {current_user.id}")
        return enterprise
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création de l'entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erreur lors de la création de l'entreprise"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la création de l'entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )

@router.put("/me", response_model=EnterpriseResponse)
async def update_my_enterprise(
    enterprise_data: EnterpriseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les informations de l'entreprise de l'utilisateur connecté
    """
    enterprise = db.query(Enterprise).filter(
        Enterprise.user_id == current_user.id
    ).first()
    
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune entreprise associée à cet utilisateur"
        )
    
    try:
        # Mettre à jour uniquement les champs fournis
        update_data = enterprise_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(enterprise, field):
                setattr(enterprise, field, value)
        
        db.commit()
        db.refresh(enterprise)
        
        logger.info(f"Entreprise mise à jour: {enterprise.name} par utilisateur {current_user.id}")
        return enterprise
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la mise à jour de l'entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de l'entreprise"
        )

@router.get("/exists")
async def check_enterprise_exists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vérifier si l'utilisateur connecté a déjà une entreprise
    Utilisé pour les guards frontend
    """
    enterprise = db.query(Enterprise).filter(
        Enterprise.user_id == current_user.id
    ).first()
    
    return {
        "exists": enterprise is not None,
        "is_complete": enterprise.is_complete if enterprise else False
    }

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_enterprise(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer l'entreprise de l'utilisateur connecté
    ⚠️ Attention: cette action est irréversible
    """
    enterprise = db.query(Enterprise).filter(
        Enterprise.user_id == current_user.id
    ).first()
    
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune entreprise associée à cet utilisateur"
        )
    
    try:
        db.delete(enterprise)
        db.commit()
        
        logger.info(f"Entreprise supprimée: {enterprise.name} par utilisateur {current_user.id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la suppression de l'entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de l'entreprise"
        )