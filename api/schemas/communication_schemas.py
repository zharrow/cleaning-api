"""
Communication Pydantic Schemas - Request/Response validation
All schemas for messaging and notification system
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


# ==================== ENUMS ====================

class SenderType(str, Enum):
    """Message sender type"""
    DEVELOPER = "Developer"
    ADMIN = "Admin"


class RecipientType(str, Enum):
    """Message/notification recipient type"""
    DEVELOPER = "Developer"
    ADMIN = "Admin"
    USER = "User"


class MessageStatus(str, Enum):
    """Message delivery status"""
    SENT = "Sent"
    DELIVERED = "Delivered"
    READ = "Read"


class NotificationPriority(str, Enum):
    """Notification priority level"""
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"


class NotificationStatus(str, Enum):
    """Notification read status"""
    UNREAD = "Unread"
    READ = "Read"
    ARCHIVED = "Archived"


# ==================== CONVERSATION SCHEMAS ====================

class ConversationCreate(BaseModel):
    """Schema for creating a conversation"""
    admin_id: uuid.UUID
    developer_id: uuid.UUID


class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: uuid.UUID
    admin_id: uuid.UUID
    developer_id: uuid.UUID
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== MESSAGE SCHEMAS ====================

class MessageCreate(BaseModel):
    """Schema for creating a message"""
    conversation_id: uuid.UUID
    sender_type: SenderType
    sender_id: uuid.UUID
    recipient_type: RecipientType
    recipient_id: uuid.UUID
    content: str


class MessageUpdate(BaseModel):
    """Schema for updating a message (mainly for marking as read)"""
    status: Optional[MessageStatus] = None


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_type: SenderType
    sender_id: uuid.UUID
    recipient_type: RecipientType
    recipient_id: uuid.UUID
    content: str
    status: MessageStatus
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== NOTIFICATION SCHEMAS ====================

class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    enterprise_id: Optional[uuid.UUID] = None
    recipient_type: RecipientType
    recipient_id: Optional[uuid.UUID] = None
    title: str = Field(..., max_length=200)
    content: str
    type: Optional[str] = Field(None, max_length=100)
    priority: NotificationPriority = NotificationPriority.INFO
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[uuid.UUID] = None


class NotificationUpdate(BaseModel):
    """Schema for updating a notification (marking as read/archived)"""
    status: Optional[NotificationStatus] = None


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: uuid.UUID
    enterprise_id: Optional[uuid.UUID]
    recipient_type: RecipientType
    recipient_id: Optional[uuid.UUID]
    title: str
    content: str
    type: Optional[str]
    priority: NotificationPriority
    status: NotificationStatus
    resource_type: Optional[str]
    resource_id: Optional[uuid.UUID]
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== WEBSOCKET SCHEMAS ====================

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str  # "message", "notification", "typing", "read_receipt", etc.
    data: dict


class TypingIndicator(BaseModel):
    """Schema for typing indicator WebSocket message"""
    conversation_id: uuid.UUID
    user_type: SenderType
    user_id: uuid.UUID
    is_typing: bool


class ReadReceipt(BaseModel):
    """Schema for read receipt WebSocket message"""
    message_id: uuid.UUID
    read_by_type: RecipientType
    read_by_id: uuid.UUID
    read_at: datetime
