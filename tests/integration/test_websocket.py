"""Tests de integración del WebSocket de pedidos/productos."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


class TestWebSocket:
    def test_ws_productos_connects(self, client: TestClient):
        """El feed de productos no requiere auth: la conexión se acepta."""
        with client.websocket_connect("/ws/productos") as ws:
            ws.send_text("ping")  # el server lo recibe en su loop; no debe cerrar

    def test_ws_pedidos_rejects_without_token(self, client: TestClient):
        """Sin token, el server acepta y cierra con código de política (1008)."""
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/pedidos") as ws:
                ws.receive_text()

    def test_ws_pedidos_rejects_invalid_token(self, client: TestClient):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/pedidos?token=token-invalido") as ws:
                ws.receive_text()

    def test_ws_pedidos_connects_with_valid_token(self, client: TestClient, admin_auth_headers: dict):
        token = admin_auth_headers["Authorization"].split(" ", 1)[1]
        with client.websocket_connect(f"/ws/pedidos?token={token}") as ws:
            ws.send_text("hola")  # conexión autenticada aceptada
