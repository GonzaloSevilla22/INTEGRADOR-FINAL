import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


def _create_pedido(client, admin_auth_headers, cliente_auth_headers):
    me = client.get("/auth/me", headers=cliente_auth_headers)
    user_id = me.json()["id"]
    addr = client.post(f"/usuarios/{user_id}/direcciones", headers=cliente_auth_headers, json={
        "alias": "Casa", "linea1": "Av. Siempre Viva 123", "ciudad": "BA", "provincia": "BA", "codigo_postal": "1000",
    })
    addr_id = addr.json()["id"]
    prod = client.post("/productos", headers=admin_auth_headers, json={
        "nombre": "Pizza", "precio_base": 10.0, "stock_manual": 10,
    })
    prod_id = prod.json()["id"]
    pedido = client.post("/pedidos", headers=cliente_auth_headers, json={
        "direccion_entrega_id": addr_id,
        "detalles": [{"producto_id": prod_id, "cantidad": 1}],
    })
    return pedido.json()["id"]


class TestPagosFlow:
    def test_create_preference_without_mp_configured(
        self, client: TestClient, admin_auth_headers: dict, cliente_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, cliente_auth_headers)
        from app.modules.payments.service import PaymentService
        with patch.object(PaymentService, "_get_mp_access_token", return_value=None):
            response = client.post(
                "/api/v1/pagos/create-preference",
                headers=cliente_auth_headers,
                json={"pedido_id": pedido_id},
            )
        assert response.status_code == 400
        assert "MercadoPago no configurado" in response.text

    def test_create_preference_success(
        self, client: TestClient, admin_auth_headers: dict, cliente_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, cliente_auth_headers)
        from app.modules.payments.service import PaymentService
        with patch.object(PaymentService, "_crear_preferencia_mp", new=AsyncMock(return_value={
            "preference_id": "pref_123",
            "init_point": "https://mercadopago.com/checkout/123",
        })):
            with patch.object(PaymentService, "_get_mp_access_token", return_value="test_token"):
                response = client.post(
                    "/api/v1/pagos/create-preference",
                    headers=cliente_auth_headers,
                    json={"pedido_id": pedido_id},
                )
        assert response.status_code == 200
        data = response.json()
        assert data["preference_id"] == "pref_123"
        assert "init_point" in data

    def test_create_preference_mp_sdk_error(
        self, client: TestClient, admin_auth_headers: dict, cliente_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, cliente_auth_headers)
        from app.modules.payments.service import PaymentService
        with patch.object(PaymentService, "_crear_preferencia_mp", new=AsyncMock(side_effect=RuntimeError("MP error"))):
            with patch.object(PaymentService, "_get_mp_access_token", return_value="test_token"):
                response = client.post(
                    "/api/v1/pagos/create-preference",
                    headers=cliente_auth_headers,
                    json={"pedido_id": pedido_id},
                )
        assert response.status_code == 400

    def test_create_preference_wrong_owner(
        self, client: TestClient, admin_auth_headers: dict, cliente_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, cliente_auth_headers)
        response = client.post(
            "/api/v1/pagos/create-preference",
            headers=admin_auth_headers,
            json={"pedido_id": pedido_id},
        )
        assert response.status_code == 403
        assert "No puedes pagar un pedido que no te pertenece" in response.text

    def test_webhook_ignores_non_payment_topic(self, client: TestClient):
        response = client.post(
            "/api/v1/pagos/webhook",
            json={"topic": "test", "id": 123},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_ignores_no_id(self, client: TestClient):
        response = client.post(
            "/api/v1/pagos/webhook",
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "No payment ID"

    def test_webhook_approved_updates_pedido(
        self, client: TestClient, admin_auth_headers: dict, cliente_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, cliente_auth_headers)
        desde = client.get(f"/pedidos/{pedido_id}", headers=cliente_auth_headers)
        assert desde.json()["estado_codigo"] == "PENDIENTE"

        from app.modules.payments.service import PaymentService
        with patch.object(PaymentService, "_crear_preferencia_mp", new=AsyncMock(return_value={
            "preference_id": "pref_abc",
            "init_point": "https://mp.com/abc",
        })):
            with patch.object(PaymentService, "_get_mp_access_token", return_value="test_token"):
                client.post(
                    "/api/v1/pagos/create-preference",
                    headers=cliente_auth_headers,
                    json={"pedido_id": pedido_id},
                )

        from app.modules.payments.service import PaymentService
        with patch.object(PaymentService, "_consultar_pago_mp", new=AsyncMock(return_value={
            "mp_payment_id": 5000,
            "mp_status": "approved",
            "mp_status_detail": "accredited",
            "mp_merchant_order_id": 9000,
        })):
            with patch.object(PaymentService, "_get_mp_access_token", return_value="test_token"):
                response = client.post(
                    "/api/v1/pagos/webhook",
                    json={"type": "payment", "data": {"id": "5000"}},
                )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert "Pago not found" in data["reason"]

    def test_redirect_after_pago_returns_redirect(self, client: TestClient):
        response = client.get("/api/v1/pagos/redirect/1/success")
        assert response.status_code == 307
        assert "orders/1/success" in response.headers.get("location", "")

    def test_confirm_payment_pedido_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        response = client.post(
            "/api/v1/pagos/confirm",
            headers=admin_auth_headers,
            json={"pedido_id": 999999},
        )
        assert response.status_code == 404

    def test_confirm_payment_without_payment_id_returns_estado_null(
        self, client: TestClient, admin_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, admin_auth_headers)
        response = client.post(
            "/api/v1/pagos/confirm",
            headers=admin_auth_headers,
            json={"pedido_id": pedido_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pedido_id"] == pedido_id

    def test_confirm_payment_with_payment_id_and_mock(
        self, client: TestClient, admin_auth_headers: dict
    ):
        pedido_id = _create_pedido(client, admin_auth_headers, admin_auth_headers)
        from app.modules.payments.service import PaymentService
        with patch.object(PaymentService, "_consultar_pago_mp", new=AsyncMock(return_value={
            "mp_payment_id": 5001,
            "mp_status": "approved",
            "mp_status_detail": "accredited",
            "mp_merchant_order_id": 9001,
        })):
            response = client.post(
                "/api/v1/pagos/confirm",
                headers=admin_auth_headers,
                json={"pedido_id": pedido_id, "payment_id": 5001},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["pedido_id"] == pedido_id
