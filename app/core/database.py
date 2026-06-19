from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=_connect_args)
_is_postgres = settings.DATABASE_URL.startswith("postgresql")


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    _migrate_legacy_schema()


def _add_column_if_missing(
    connection, table: str, column_name: str, column_def: str
) -> None:
    inspector = inspect(connection)
    if table not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns(table)}
    if column_name in columns:
        return
    if _is_postgres:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))
    else:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))


def _update_activo_from_deleted_at(connection, table: str) -> None:
    inspector = inspect(connection)
    if table not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns(table)}
    if "activo" not in columns:
        return
    connection.execute(
        text(
            f"UPDATE {table} SET activo = CASE "
            "WHEN deleted_at IS NULL THEN TRUE ELSE FALSE END "
            "WHERE activo IS NULL"
        )
    )


def _migrate_legacy_schema() -> None:
    """Aplicar ajustes mínimos sobre tablas existentes sin migraciones formales.
    Cada operación DDL se ejecuta en su propia transacción para compatibilidad
    con PostgreSQL (que requiere commit implícito en ciertas ALTER TABLE)."""
    with engine.connect() as connection:
        _add_column_if_missing(
            connection, "categorias", "activo", "activo BOOLEAN NOT NULL DEFAULT TRUE"
        )
        _add_column_if_missing(
            connection, "categorias", "parent_id", "parent_id INTEGER"
        )
        _update_activo_from_deleted_at(connection, "categorias")

        _add_column_if_missing(
            connection, "productos_ingredientes", "cantidad", "cantidad DOUBLE PRECISION NOT NULL DEFAULT 1"
        )
        _add_column_if_missing(
            connection, "productos_ingredientes", "unidad", "unidad VARCHAR(20) NOT NULL DEFAULT 'gramos'"
        )
        _add_column_if_missing(
            connection, "productos_ingredientes", "es_removible", "es_removible BOOLEAN NOT NULL DEFAULT false"
        )
        _add_column_if_missing(
            connection, "productos_ingredientes", "es_opcional", "es_opcional BOOLEAN NOT NULL DEFAULT false"
        )

        _add_column_if_missing(
            connection, "ingredientes", "stock_actual", "stock_actual DOUBLE PRECISION NOT NULL DEFAULT 0"
        )
        _add_column_if_missing(
            connection, "ingredientes", "stock_minimo", "stock_minimo DOUBLE PRECISION NOT NULL DEFAULT 0"
        )
        _add_column_if_missing(
            connection, "ingredientes", "costo_unitario", "costo_unitario NUMERIC(10,4) NOT NULL DEFAULT 0"
        )
        _add_column_if_missing(
            connection, "ingredientes", "unidad_medida", "unidad_medida VARCHAR(20) NOT NULL DEFAULT 'gramos'"
        )
        _add_column_if_missing(
            connection, "ingredientes", "activo", "activo BOOLEAN NOT NULL DEFAULT TRUE"
        )
        _update_activo_from_deleted_at(connection, "ingredientes")

        _add_column_if_missing(
            connection, "productos", "usa_stock_manual", "usa_stock_manual BOOLEAN NOT NULL DEFAULT FALSE"
        )
        _add_column_if_missing(
            connection, "productos", "stock_manual", "stock_manual INTEGER"
        )
        _add_column_if_missing(
            connection, "productos", "costo_compra_manual", "costo_compra_manual NUMERIC(10,4)"
        )
        _add_column_if_missing(
            connection, "productos", "activo", "activo BOOLEAN NOT NULL DEFAULT TRUE"
        )
        _update_activo_from_deleted_at(connection, "productos")

        _add_column_if_missing(
            connection, "pedidos", "forma_pago_codigo", "forma_pago_codigo VARCHAR(50)"
        )

    # Migrar estados legacy en transacción separada con commit explícito
    # (engine.connect() no hace commit automático, y el seed necesita ver estos cambios)
    with engine.begin() as conn:
        _migrate_estado_pedido(conn, "CONFIRMADO", "PAGADO")
        _migrate_estado_pedido(conn, "EN_PREP", "EN_PREPARACION")
        _migrate_estado_pedido(conn, "PREPARANDO", "EN_PREPARACION")
        _migrate_estado_pedido(conn, "EN_CAMINO", "EN_PREPARACION")


_ESTADO_INFO = {
    "PENDIENTE": ("Pendiente", "Pedido creado, aguardando pago"),
    "PAGADO": ("Pagado", "Pedido pagado, pendiente de preparación"),
    "EN_PREPARACION": ("En Preparación", "Pedido en preparación"),
    "TERMINADO": ("Terminado", "Pedido terminado, listo para entregar"),
    "ENTREGADO": ("Entregado", "Pedido entregado al cliente"),
    "CANCELADO": ("Cancelado", "Pedido cancelado"),
}


def _migrate_estado_pedido(connection, old_codigo: str, new_codigo: str) -> None:
    """Migrar pedidos e historiales de un estado antiguo a uno nuevo.

    También asegura que el estado nuevo exista en la tabla estados_pedido.
    """
    inspector = inspect(connection)
    for table in ("pedidos", "historiales_estado_pedido"):
        if table not in inspector.get_table_names():
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        col = "estado_codigo" if table == "pedidos" else "estado_desde_codigo"
        if col in columns:
            connection.execute(
                text(f"UPDATE {table} SET {col} = :new WHERE {col} = :old").bindparams(
                    new=new_codigo, old=old_codigo
                )
            )
        col2 = "estado_hacia_codigo" if table == "historiales_estado_pedido" else None
        if col2 and col2 in columns:
            connection.execute(
                text(f"UPDATE {table} SET {col2} = :new WHERE {col2} = :old").bindparams(
                    new=new_codigo, old=old_codigo
                )
            )

    # Asegurar que el estado nuevo exista en estados_pedido
    if "estados_pedido" in inspector.get_table_names():
        info = _ESTADO_INFO.get(new_codigo, (new_codigo, ""))
        if _is_postgres:
            connection.execute(
                text(
                    "INSERT INTO estados_pedido (codigo, nombre, descripcion) "
                    "VALUES (:codigo, :nombre, :descripcion) ON CONFLICT (codigo) DO NOTHING"
                ).bindparams(codigo=new_codigo, nombre=info[0], descripcion=info[1])
            )
        else:
            connection.execute(
                text(
                    "INSERT OR IGNORE INTO estados_pedido (codigo, nombre, descripcion) "
                    "VALUES (:codigo, :nombre, :descripcion)"
                ).bindparams(codigo=new_codigo, nombre=info[0], descripcion=info[1])
            )

    # Eliminar estado antiguo si existe en estados_pedido
    if "estados_pedido" in inspector.get_table_names():
        connection.execute(
            text("DELETE FROM estados_pedido WHERE codigo = :old").bindparams(old=old_codigo)
        )


def get_session():
    with Session(engine) as session:
        yield session
