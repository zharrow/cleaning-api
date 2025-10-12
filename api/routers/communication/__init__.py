"""
Communication Routers Package
Organize all communication-related API endpoints (messaging, notifications, WebSocket)
"""

from fastapi import APIRouter
from . import conversations, messages, notifications, websocket

# Create main Communication router
router = APIRouter()

# Include all sub-routers
router.include_router(conversations.router, prefix="/conversations", tags=["Communication - Conversations"])
router.include_router(messages.router, prefix="/messages", tags=["Communication - Messages"])
router.include_router(notifications.router, prefix="/notifications", tags=["Communication - Notifications"])
router.include_router(websocket.router, tags=["Communication - WebSocket"])
