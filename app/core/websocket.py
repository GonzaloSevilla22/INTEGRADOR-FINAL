import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("app.core.websocket")


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("Nueva conexion websocket. Activas=%s", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("Conexion websocket cerrada. Activas=%s", len(self.active_connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        if not self.active_connections:
            return

        payload = {"event": event_type, "data": data}
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                self.active_connections.discard(connection)


manager = ConnectionManager()
