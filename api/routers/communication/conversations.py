"""
Communication Router - Conversations
Handles CRUD operations for conversations between admins and developers
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.core.security import get_current_admin, get_current_developer
from api.models.user import Admin, Developer
from api.models.communication_models import Conversation
from api.schemas.communication_schemas import ConversationCreate, ConversationResponse

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create a new conversation between admin and developer"""
    # Check if conversation already exists
    existing = db.query(Conversation).filter(
        Conversation.admin_id == conversation.admin_id,
        Conversation.developer_id == conversation.developer_id
    ).first()

    if existing:
        return existing

    db_conversation = Conversation(**conversation.dict())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all conversations for current admin"""
    return db.query(Conversation).filter(
        Conversation.admin_id == current_admin.id
    ).order_by(Conversation.last_message_at.desc()).all()


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific conversation by ID"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.admin_id == current_admin.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable"
        )
    return conversation
