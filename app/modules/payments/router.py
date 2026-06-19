import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_roles
from app.modules.usuarios.schemas import CurrentUser
from app.modules.payments.schemas import (
    CrearPagoRequest,
    ConfirmarPagoRequest,
    PagoCrearResponse,
    PagoEstadoResponse,
    PagoPublic,
    ManualAprobarRequest,
)
from app.modules.payments.service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pagos", tags=["pagos"])


def get_payment_service(session: Session = Depends(get_session)) -> PaymentService:
    return PaymentService(session)


@router.post("/crear", response_model=PagoCrearResponse)
@router.post("/create-preference", response_model=PagoCrearResponse)
async def create_preference(
    data: CrearPagoRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    svc: PaymentService = Depends(get_payment_service),
):
    return await svc.crear_pago(data.pedido_id, current_user.id)


@router.get("/{pedido_id}", response_model=PagoPublic)
def get_pago_by_pedido(
    pedido_id: int,
    svc: PaymentService = Depends(get_payment_service),
):
    return svc.obtener_pago_por_pedido(pedido_id)


@router.post("/manual-aprobar", response_model=PagoEstadoResponse)
async def manual_aprobar(
    data: ManualAprobarRequest,
    _: CurrentUser = Depends(require_roles(["ADMIN", "PEDIDOS"])),
    svc: PaymentService = Depends(get_payment_service),
):
    return await svc.aprobar_manual(data)


@router.post("/webhook")
async def webhook(
    request: Request,
    svc: PaymentService = Depends(get_payment_service),
):
    try:
        query_params = dict(request.query_params)
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
        else:
            data = dict(await request.form())
        return await svc.procesar_webhook(data, query_params=query_params)
    except Exception as e:
        logger.exception("Error en webhook MP")
        return {"status": "error", "reason": str(e)}


@router.post("/confirm", response_model=PagoEstadoResponse)
async def confirm_payment(
    data: ConfirmarPagoRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    svc: PaymentService = Depends(get_payment_service),
):
    """Confirmar/verificar pago. Puede ser llamado por el dueño del pedido o admin/pedidos."""
    return await svc.confirmar_pago(data.pedido_id, data.payment_id, current_user)


@router.get("/verify/{pedido_id}", response_model=PagoEstadoResponse)
async def verify_payment(
    pedido_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    svc: PaymentService = Depends(get_payment_service),
):
    """Verificar el estado real del pago contra MercadoPago. Puede ser llamado por el cliente."""
    return await svc.confirmar_pago(pedido_id, payment_id=None, current_user=current_user)


@router.get("/redirect/{pedido_id}/{status}")
async def redirect_after_pago(pedido_id: int, status: str, request: Request):
    frontend_url = settings.VITE_FRONTEND_URL or "http://localhost:5500"
    url = f"{frontend_url}/pedido/{pedido_id}?status={status}"
    qs = request.url.query
    if qs and "status=" not in qs:
        url += f"&{qs}"
    return RedirectResponse(url=url)
