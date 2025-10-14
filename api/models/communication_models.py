"""
Communication Models - Messaging and Notification System
Supports real-time messaging (Admin ↔ Developer) and notifications
"""

from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from api.models.base import TimestampedModel, BaseModel


# ==================== ENUMS ====================

class SenderType(PyEnum):
    """Message sender type"""
    DEVELOPER = "Developer"
    ADMIN = "Admin"


class RecipientType(PyEnum):
    """Message/notification recipient type"""
    DEVELOPER = "Developer"
    ADMIN = "Admin"
    USER = "User"


class MessageStatus(PyEnum):
    """Message delivery status"""
    SENT = "Sent"
    DELIVERED = "Delivered"
    READ = "Read"


class NotificationPriority(PyEnum):
    """Notification priority level"""
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"


class NotificationStatus(PyEnum):
    """Notification read status"""
    UNREAD = "Unread"
    READ = "Read"
    ARCHIVED = "Archived"


# ==================== MODELS ====================

class Conversation(TimestampedModel):
    """
    Conversation thread between an admin and a developer
    Groups messages like Messenger conversations
    """
    __tablename__ = "conversation"

    admin_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    developer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("developer.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    last_message_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last message timestamp for sorting"
    )

    # Relationships
    admin = relationship("Admin", backref="conversations")
    developer = relationship("Developer", backref="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    # Unique constraint: prevent duplicate conversations
    __table_args__ = (
        UniqueConstraint('admin_id', 'developer_id', name='uq_admin_developer_conversation'),
    )

    def __repr__(self):
        return f"<Conversation(id='{self.id}', admin='{self.admin_id}', developer='{self.developer_id}')>"


class Message(BaseModel):
    """
    Internal messaging system (Admin ↔ Developer) with WebSocket support
    When sent, automatically creates a notification for recipient
    """
    __tablename__ = "message"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Groups messages in a conversation thread"
    )

    sender_type = Column(
        Enum(SenderType),
        nullable=False,
        comment="Sender type (Developer or Admin)"
    )

    sender_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Sender ID (developer.id or admin.id)"
    )

    recipient_type = Column(
        Enum(RecipientType),
        nullable=False,
        comment="Recipient type (Developer or Admin)"
    )

    recipient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Recipient ID (developer.id or admin.id)"
    )

    content = Column(Text, nullable=False, comment="Message content")

    status = Column(
        Enum(MessageStatus),
        default=MessageStatus.SENT,
        nullable=False,
        comment="Message status"
    )

    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date marked as read"
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id='{self.id}', sender='{self.sender_type.value}', status='{self.status.value}')>"


class Notification(BaseModel):
    """
    Notification system for all user types (Developer, Admin, User)

    Use cases:
    - HACCP alerts (temperature out of range, expiry approaching)
    - Task reminders (overdue tasks, scheduled tasks)
    - System notifications (new features, maintenance)
    - Message notifications (new message received)

    Broadcasting: recipient_id null = broadcast to all users of recipient_type in enterprise
    System-wide: enterprise_id null = system notification (e.g., developer → all admins)
    """
    __tablename__ = "notification"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Enterprise (null for system-wide notifications)"
    )

    recipient_type = Column(
        Enum(RecipientType),
        nullable=False,
        comment="Type of recipient (Developer, Admin, or User)"
    )

    recipient_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Specific recipient (null = broadcast to all of recipient_type)"
    )

    title = Column(String(200), nullable=False, comment="Notification title")
    content = Column(Text, nullable=False, comment="Notification content")

    type = Column(
        String(100),
        nullable=True,
        comment="Type/category (HACCP, Task, System, Message, etc.)"
    )

    priority = Column(
        Enum(NotificationPriority),
        default=NotificationPriority.INFO,
        nullable=False,
        comment="Notification priority"
    )

    status = Column(
        Enum(NotificationStatus),
        default=NotificationStatus.UNREAD,
        nullable=False,
        comment="Read status"
    )

    resource_type = Column(
        String(50),
        nullable=True,
        comment="Resource type (meal, task, equipment, message, etc.)"
    )

    resource_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Link to related resource (polymorphic)"
    )

    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date marked as read"
    )

    # Relationships
    enterprise = relationship("Enterprise", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id='{self.id}', type='{self.type}', priority='{self.priority.value}', status='{self.status.value}')>"
