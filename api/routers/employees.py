"""
Router for User (Employee) management
Users are staff members created by Admins with PIN authentication
Users can access multiple rooms within their enterprise
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import hashlib

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User, Admin, UserRooms
from api.models.enterprise import Enterprise
from api.models.room import Room
from api.schemas.user_schemas import (
    UserCreate, UserUpdate, UserResponse, UserLoginRequest, UserLoginResponse,
    UserRoomCreate, UserRoomResponse
)

router = APIRouter(prefix="/employees", tags=["Employees"])


def hash_pin(pin: str) -> str:
    """Hash a PIN code for secure storage"""
    return hashlib.sha256(pin.encode()).hexdigest()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    user: UserCreate,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new User (employee) account
    NOTE: Should be called by Admin only
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Check if PIN already exists in this enterprise
    hashed_pin = hash_pin(user.pin_code)
    existing = db.query(User).filter(
        User.enterprise_id == enterprise.id,
        User.pin_code == hashed_pin
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN code already in use in this enterprise"
        )

    # Create user
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        pin_code=hashed_pin,
        enterprise_id=enterprise.id,
        created_by_id=current_user.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("", response_model=List[UserResponse])
async def list_employees(
    current_user: Admin = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all employees for an admin's enterprise
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Get users in this enterprise
    users = db.query(User).filter(
        User.enterprise_id == enterprise.id
    ).offset(skip).limit(limit).all()

    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_employee(
    user_id: str,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee by ID
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.enterprise_id == enterprise.id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_employee(
    user_id: str,
    user_update: UserUpdate,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update employee information
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.enterprise_id == enterprise.id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)

    # Hash PIN if provided
    if "pin_code" in update_data and update_data["pin_code"]:
        # Check if new PIN already exists
        hashed_pin = hash_pin(update_data["pin_code"])
        existing = db.query(User).filter(
            User.enterprise_id == enterprise.id,
            User.pin_code == hashed_pin,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PIN code already in use in this enterprise"
            )
        update_data["pin_code"] = hashed_pin

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    user_id: str,
    current_user: Admin = Depends(get_current_user),
    hard_delete: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete an employee
    - Soft delete (default): sets is_active=False
    - Hard delete: permanently removes from database (fails if user has task/log references)
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.enterprise_id == enterprise.id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if hard_delete:
        # Hard delete - will fail if user has references
        try:
            db.delete(user)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete user with existing task/log references. Use soft delete instead. Error: {str(e)}"
            )
    else:
        # Soft delete
        user.is_active = False
        db.commit()

    return None


# ==================== USER AUTHENTICATION ====================

@router.post("/login", response_model=UserLoginResponse)
async def login_employee(
    login: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate employee with PIN code
    Returns user info and accessible rooms
    """
    hashed_pin = hash_pin(login.pin_code)

    # Find user by PIN and enterprise
    user = db.query(User).filter(
        User.enterprise_id == login.enterprise_id,
        User.pin_code == hashed_pin,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN code or user not found"
        )

    # Get accessible rooms
    user_rooms = db.query(UserRooms).filter(UserRooms.user_id == user.id).all()
    accessible_room_ids = [ur.room_id for ur in user_rooms]

    return UserLoginResponse(
        user=user,
        accessible_rooms=accessible_room_ids
    )


# ==================== ROOM ACCESS MANAGEMENT ====================

@router.post("/{user_id}/rooms", response_model=UserRoomResponse, status_code=status.HTTP_201_CREATED)
async def grant_room_access(
    user_id: str,
    room_access: UserRoomCreate,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Grant room access to an employee
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Verify user exists and belongs to this enterprise
    user = db.query(User).filter(
        User.id == user_id,
        User.enterprise_id == enterprise.id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Verify room exists and belongs to this enterprise
    room = db.query(Room).filter(
        Room.id == room_access.room_id,
        Room.enterprise_id == enterprise.id
    ).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found in this enterprise"
        )

    # Check if access already exists
    existing = db.query(UserRooms).filter(
        UserRooms.user_id == user_id,
        UserRooms.room_id == room_access.room_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has access to this room"
        )

    # Grant access
    user_room = UserRooms(user_id=user_id, room_id=room_access.room_id)
    db.add(user_room)
    db.commit()
    db.refresh(user_room)

    return user_room


@router.get("/{user_id}/rooms", response_model=List[UserRoomResponse])
async def list_employee_rooms(
    user_id: str,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all rooms accessible by an employee
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Verify user exists and belongs to this enterprise
    user = db.query(User).filter(
        User.id == user_id,
        User.enterprise_id == enterprise.id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Get accessible rooms
    user_rooms = db.query(UserRooms).filter(UserRooms.user_id == user_id).all()
    return user_rooms


@router.delete("/{user_id}/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_room_access(
    user_id: str,
    room_id: str,
    current_user: Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke room access from an employee
    """
    # Get admin's enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.admin_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin does not have an enterprise"
        )

    # Verify user exists and belongs to this enterprise
    user = db.query(User).filter(
        User.id == user_id,
        User.enterprise_id == enterprise.id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Find and delete access
    user_room = db.query(UserRooms).filter(
        UserRooms.user_id == user_id,
        UserRooms.room_id == room_id
    ).first()

    if not user_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room access not found"
        )

    db.delete(user_room)
    db.commit()
    return None
