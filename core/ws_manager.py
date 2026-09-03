import json
from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: Dict[str, Any]):
        message_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                # Connection might be dropped
                self.disconnect(connection)

ws_manager = WebSocketManager()
