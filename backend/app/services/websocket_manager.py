import json
from typing import Dict
from fastapi import WebSocket
from app.models.request import LLMRequest


class ConnectionManager:
    """
    Manages WebSocket connections to UI operators.

    Key responsibilities:
    - Track active connections (user_id -> WebSocket)
    - Send messages to specific users or broadcast to all
    - Handle connection/disconnection
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected: {user_id}")

    async def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket disconnected: {user_id}")

    async def send_personal(self, user_id: str, message: dict):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
                await self.disconnect(user_id)

    async def broadcast(self, message: dict):
        """Send message to all connected users"""
        disconnected = []

        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to {user_id}: {e}")
                disconnected.append(user_id)

        # Cleanup disconnected users
        for user_id in disconnected:
            await self.disconnect(user_id)

    async def broadcast_new_request(self, request: LLMRequest):
        """Broadcast a new LLM request to all operators"""
        message = {
            "type": "new_request",
            "data": request.dict()
        }
        # Convert datetime objects to ISO format strings
        if "timestamp" in message["data"]:
            message["data"]["timestamp"] = message["data"]["timestamp"].isoformat()
        if "timeout_at" in message["data"]:
            message["data"]["timeout_at"] = message["data"]["timeout_at"].isoformat()
        await self.broadcast(message)

    async def broadcast_request_cancelled(self, request_id: str, reason: str):
        """Broadcast that a request was cancelled"""
        message = {
            "type": "request_cancelled",
            "data": {
                "request_id": request_id,
                "reason": reason
            }
        }
        await self.broadcast(message)

    async def broadcast_timeout_warning(self, request_id: str, seconds_remaining: int):
        """Broadcast timeout warning"""
        message = {
            "type": "request_timeout_warning",
            "data": {
                "request_id": request_id,
                "seconds_remaining": seconds_remaining
            }
        }
        await self.broadcast(message)

    async def broadcast_stats(self, stats: dict):
        """Broadcast stats update"""
        message = {
            "type": "stats_update",
            "data": stats
        }
        await self.broadcast(message)

    async def send_error(self, user_id: str, error_code: str, error_message: str, request_id: str | None = None):
        """Send error message to a specific user"""
        message = {
            "type": "error",
            "data": {
                "error_code": error_code,
                "message": error_message
            }
        }
        if request_id:
            message["data"]["request_id"] = request_id

        await self.send_personal(user_id, message)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def is_connected(self, user_id: str) -> bool:
        """Check if a user is connected"""
        return user_id in self.active_connections


# Global singleton instance
websocket_manager = ConnectionManager()
