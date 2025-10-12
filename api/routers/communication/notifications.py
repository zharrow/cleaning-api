"""
Communication Router - Notifications
Handles notifications for all user types (Developer, Admin, User)
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.core.security import get_current_admin
from api.models.user import Admin
from api.models.communication_models import Notification
from api.schemas.communication_schemas import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationStatus
)

router = APIRouter()


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create a new notification (Admin only)"""
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    status_filter: Optional[NotificationStatus] = None,
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all notifications for current admin"""
    query = db.query(Notification).filter(
        Notification.recipient_type == "Admin",
        (Notification.recipient_id == current_admin.id) |
        (Notification.recipient_id.is_(None))
    )

    if status_filter:
        query = query.filter(Notification.status == status_filter)

    if type_filter:
        query = query.filter(Notification.type == type_filter)

    return query.order_by(Notification.created_at.desc()).all()


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific notification by ID"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_type == "Admin",
        (Notification.recipient_id == current_admin.id) |
        (Notification.recipient_id.is_(None))
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable"
        )
    return notification


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: UUID,
    payload: NotificationUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update notification status (mark as read/archived)"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_type == "Admin",
        (Notification.recipient_id == current_admin.id) |
        (Notification.recipient_id.is_(None))
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable"
        )

    if payload.status == NotificationStatus.READ:
        notification.read_at = datetime.utcnow()

    notification.status = payload.status
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_type == "Admin",
        (Notification.recipient_id == current_admin.id) |
        (Notification.recipient_id.is_(None))
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable"
        )

    db.delete(notification)
    db.commit()
    return None


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Mark all unread notifications as read"""
    notifications = db.query(Notification).filter(
        Notification.recipient_type == "Admin",
        (Notification.recipient_id == current_admin.id) |
        (Notification.recipient_id.is_(None)),
        Notification.status == NotificationStatus.UNREAD
    ).all()

    for notification in notifications:
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()

    db.commit()
    return {"message": f"{len(notifications)} notifications marquées comme lues"}
