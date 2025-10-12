from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.models.base import TimestampedModel
from enum import Enum as PyEnum
import uuid

# ==================== LEGACY USER ROLE (For backward compatibility) ====================
class UserRole(PyEnum):
    """
    DEPRECATED: Legacy user roles for old authentication system
    Use Developer, Admin, User models instead
    """
    ADMIN = "admin"
    MANAGER = "manager"
    GERANTE = "gerante"  # Legacy role

# ==================== DEVELOPER ====================
class Developer(TimestampedModel):
    """Super administrator with analytics view only"""
    __tablename__ = "developer"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Optional if only Firebase
    firebase_uid = Column(String(255), unique=True, nullable=False, index=True)

    # Relationships
    admins = relationship("Admin", back_populates="developer", cascade="all, delete-orphan")

# ==================== ADMIN ====================
class Admin(TimestampedModel):
    """Daycare/micro-daycare manager with full back-office access"""
    __tablename__ = "admin"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Optional if only Firebase
    firebase_uid = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("developer.id"), nullable=False)

    # Relationships
    developer = relationship("Developer", back_populates="admins")
    enterprise = relationship("Enterprise", back_populates="admin", uselist=False)
    users = relationship("User", back_populates="admin", cascade="all, delete-orphan")

# ==================== USER (Employee) ====================
class User(TimestampedModel):
    """Employee/staff member with PIN authentication for tablet access"""
    __tablename__ = "user"

    email = Column(String(255), nullable=True, index=True)  # Optional
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    pin_code = Column(String(64), nullable=False)  # SHA256 hash of 4-6 digit PIN
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("admin.id"), nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="users")
    admin = relationship("Admin", back_populates="users")
    user_rooms = relationship("UserRooms", back_populates="user", cascade="all, delete-orphan")

    # Task relationships
    assigned_tasks = relationship("AssignedTask", foreign_keys="[AssignedTask.default_performer_id]", back_populates="default_performer")
    performed_logs = relationship("CleaningLog", foreign_keys="[CleaningLog.performed_by_id]", back_populates="performed_by")
    recorded_logs = relationship("CleaningLog", foreign_keys="[CleaningLog.recorded_by_id]", back_populates="recorded_by")

    # HACCP relationships (responsible_id)
    meals = relationship("Meal", foreign_keys="[Meal.responsible_id]", back_populates="responsible")
    temperatures = relationship("Temperature", foreign_keys="[Temperature.responsible_id]", back_populates="responsible")
    cleaning_haccp_records = relationship("CleaningHaccp", foreign_keys="[CleaningHaccp.responsible_id]", back_populates="responsible")
    non_compliances = relationship("NonCompliance", foreign_keys="[NonCompliance.responsible_id]", back_populates="responsible")
    documents = relationship("Document", foreign_keys="[Document.responsible_id]", back_populates="responsible")

# ==================== USER_ROOMS (Associative) ====================
class UserRooms(TimestampedModel):
    """Many-to-many relationship: users can access multiple rooms"""
    __tablename__ = "user_rooms"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="user_rooms")
    room = relationship("Room", back_populates="user_rooms")

    # Unique constraint: prevent duplicate user-room pairs
    __table_args__ = (
        UniqueConstraint('user_id', 'room_id', name='uq_user_room'),
    )