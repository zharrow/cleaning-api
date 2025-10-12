"""
Communication Router - Messages
Handles messaging between admins and developers with WebSocket support
"""

from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.communication_models import Message, Conversation, Notification
from api.schemas.communication_schemas import (
    MessageCreate, MessageUpdate, MessageResponse,
    NotificationCreate, MessageStatus
)

router = APIRouter()


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Send a message and create notification for recipient"""
    # Verify conversation exists and admin has access
    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.admin_id == current_admin.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable"
        )

    # Create message
    db_message = Message(**message.dict())
    db.add(db_message)

    # Update conversation last_message_at
    conversation.last_message_at = datetime.utcnow()

    # Create notification for recipient
    notification = Notification(
        enterprise_id=current_admin.enterprise.id if message.recipient_type == "Admin" else None,
        recipient_type=message.recipient_type,
        recipient_id=message.recipient_id,
        title="Nouveau message",
        content=f"Message de {current_admin.first_name} {current_admin.last_name}",
        type="Message",
        priority="Info",
        resource_type="message",
        resource_id=db_message.id
    )
    db.add(notification)

    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all messages for a conversation"""
    # Verify conversation access
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.admin_id == current_admin.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable"
        )

    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message_status(
    message_id: UUID,
    payload: MessageUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update message status (mark as read, delivered, etc.)"""
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message introuvable"
        )

    # Verify admin is the recipient
    if message.recipient_id != current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non autorisé à modifier ce message"
        )

    if payload.status == MessageStatus.READ:
        message.read_at = datetime.utcnow()

    message.status = payload.status
    db.commit()
    db.refresh(message)
    return message


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific message by ID"""
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message introuvable"
        )

    # Verify admin has access (either sender or recipient)
    if message.sender_id != current_admin.id and message.recipient_id != current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )

    return message
