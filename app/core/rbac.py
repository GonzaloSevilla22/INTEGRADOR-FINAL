"""Constantes y helpers de RBAC."""

ROLE_ADMIN = "ADMIN"
ROLE_STOCK = "STOCK"
ROLE_PEDIDOS = "PEDIDOS"
ROLE_CLIENT = "CLIENT"

ALL_ROLES = [ROLE_ADMIN, ROLE_STOCK, ROLE_PEDIDOS, ROLE_CLIENT]

# Estados de pedido
STATE_PENDIENTE = "PENDIENTE"
STATE_PAGADO = "PAGADO"
STATE_EN_PREPARACION = "EN_PREPARACION"
STATE_TERMINADO = "TERMINADO"
STATE_ENTREGADO = "ENTREGADO"
STATE_CANCELADO = "CANCELADO"

# Mapeo de estados legacy → nuevos (para migración)
STATE_LEGACY_MAP = {
    "CONFIRMADO": STATE_PAGADO,
    "EN_PREP": STATE_EN_PREPARACION,
}

ALL_STATES = [
    STATE_PENDIENTE,
    STATE_PAGADO,
    STATE_EN_PREPARACION,
    STATE_TERMINADO,
    STATE_ENTREGADO,
    STATE_CANCELADO,
]

# Estados terminales (no permiten modificaciones posteriores)
TERMINAL_STATES = {STATE_ENTREGADO, STATE_CANCELADO}


def normalize_role(role: str) -> str:
    return (role or "").strip().upper()


def normalize_state(state: str) -> str:
    raw = (state or "").strip().upper()
    # Mapear estados legacy
    if raw == "PREPARANDO":
        return STATE_EN_PREPARACION
    if raw == "CONFIRMADO":
        return STATE_PAGADO
    if raw == "EN_PREP":
        return STATE_EN_PREPARACION
    if raw == "EN_CAMINO":
        return STATE_EN_PREPARACION
    return raw


def is_terminal(state: str) -> bool:
    return normalize_state(state) in TERMINAL_STATES
