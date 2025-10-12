"""
Communication Router - WebSocket
Real-time messaging and notifications via WebSocket
"""

from typing import Dict
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import logging

from api.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""

    def __init__(self):
        # Active connections: {user_type: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[UUID, WebSocket]] = {
            "Developer": {},
            "Admin": {},
            "User": {}
        }

    async def connect(self, websocket: WebSocket, user_type: str, user_id: UUID):
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        if user_type not in self.active_connections:
            self.active_connections[user_type] = {}
        self.active_connections[user_type][user_id] = websocket
        logger.info(f"{user_type} {user_id} connected via WebSocket")

    def disconnect(self, user_type: str, user_id: UUID):
        """Remove a WebSocket connection"""
        if user_type in self.active_connections and user_id in self.active_connections[user_type]:
            del self.active_connections[user_type][user_id]
            logger.info(f"{user_type} {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: dict, user_type: str, user_id: UUID):
        """Send a message to a specific user"""
        if user_type in self.active_connections and user_id in self.active_connections[user_type]:
            websocket = self.active_connections[user_type][user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_type} {user_id}: {e}")
                self.disconnect(user_type, user_id)

    async def send_to_enterprise(self, message: dict, enterprise_id: UUID, user_type: str = None):
        """Send a message to all users of an enterprise (optionally filtered by user_type)"""
        # This would require enterprise_id tracking in connections
        # For now, broadcast to all of user_type
        if user_type:
            await self.broadcast_to_type(message, user_type)

    async def broadcast_to_type(self, message: dict, user_type: str):
        """Broadcast message to all users of a specific type"""
        if user_type not in self.active_connections:
            return

        disconnected = []
        for user_id, websocket in self.active_connections[user_type].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {user_type} {user_id}: {e}")
                disconnected.append((user_type, user_id))

        # Clean up disconnected clients
        for ut, uid in disconnected:
            self.disconnect(ut, uid)

    async def broadcast_all(self, message: dict):
        """Broadcast message to all connected users"""
        for user_type in self.active_connections:
            await self.broadcast_to_type(message, user_type)


manager = ConnectionManager()


@router.websocket("/ws/{user_type}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_type: str,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time communication

    Usage:
    - ws://localhost:8000/api/communication/ws/Admin/{admin_id}
    - ws://localhost:8000/api/communication/ws/Developer/{developer_id}
    - ws://localhost:8000/api/communication/ws/User/{user_id}
    """
    if user_type not in ["Developer", "Admin", "User"]:
        await websocket.close(code=1008, reason="Invalid user type")
        return

    await manager.connect(websocket, user_type, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle different message types
            message_type = message_data.get("type")

            if message_type == "typing":
                # Broadcast typing indicator
                recipient_type = message_data.get("recipient_type")
                recipient_id = UUID(message_data.get("recipient_id"))
                await manager.send_personal_message(
                    {
                        "type": "typing",
                        "sender_type": user_type,
                        "sender_id": str(user_id),
                        "is_typing": message_data.get("is_typing", True)
                    },
                    recipient_type,
                    recipient_id
                )

            elif message_type == "read_receipt":
                # Send read receipt
                recipient_type = message_data.get("recipient_type")
                recipient_id = UUID(message_data.get("recipient_id"))
                await manager.send_personal_message(
                    {
                        "type": "read_receipt",
                        "message_id": message_data.get("message_id"),
                        "read_by_type": user_type,
                        "read_by_id": str(user_id)
                    },
                    recipient_type,
                    recipient_id
                )

            elif message_type == "message":
                # New message notification (handled by message router)
                # This is just for real-time delivery
                recipient_type = message_data.get("recipient_type")
                recipient_id = UUID(message_data.get("recipient_id"))
                await manager.send_personal_message(
                    {
                        "type": "new_message",
                        "message": message_data.get("content"),
                        "sender_type": user_type,
                        "sender_id": str(user_id),
                        "conversation_id": message_data.get("conversation_id")
                    },
                    recipient_type,
                    recipient_id
                )

            elif message_type == "notification":
                # New notification (broadcast or targeted)
                if message_data.get("broadcast"):
                    await manager.broadcast_to_type(
                        {
                            "type": "notification",
                            "notification": message_data.get("notification")
                        },
                        message_data.get("target_type", "Admin")
                    )
                else:
                    recipient_type = message_data.get("recipient_type")
                    recipient_id = UUID(message_data.get("recipient_id"))
                    await manager.send_personal_message(
                        {
                            "type": "notification",
                            "notification": message_data.get("notification")
                        },
                        recipient_type,
                        recipient_id
                    )

    except WebSocketDisconnect:
        manager.disconnect(user_type, user_id)
        logger.info(f"Client {user_type} {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {user_type} {user_id}: {e}")
        manager.disconnect(user_type, user_id)
