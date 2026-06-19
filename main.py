import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.seed import initialize_roles_and_states
from app.modules.auth.router import router as auth_router
from app.modules.usuarios.router import router as usuarios_router
from app.modules.categorias.router import router as categorias_router
from app.modules.ingredientes.router import router as ingredientes_router
from app.modules.productos.router import router as productos_router
from app.modules.pedidos.router import router as pedidos_router
from app.modules.payments.router import router as pagos_router
from app.modules.estadisticas.router import router as estadisticas_router
from app.modules.uploads.router import router as uploads_router
from app.modules.direcciones.router import router as direcciones_router
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging_middleware import LoggingMiddleware
from app.core.exception_handlers import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-16s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    initialize_roles_and_states()
    yield


app = FastAPI(
    title="Food Store API",
    description="Backend de Programacion 4 - Tienda de Comida",
    version="2.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)

# Routers de autenticación y usuarios
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(usuarios_router, prefix="/usuarios", tags=["usuarios"])

# Routers de catálogo
app.include_router(categorias_router, prefix="/categorias", tags=["categorias"])
app.include_router(productos_router, prefix="/productos", tags=["productos"])
app.include_router(ingredientes_router, prefix="/ingredientes", tags=["ingredientes"])

# Router de direcciones
app.include_router(direcciones_router)

# Router de pedidos
app.include_router(pedidos_router, prefix="/pedidos", tags=["pedidos"])

# Router de pagos (MercadoPago)
app.include_router(pagos_router)

# Router de estadísticas
app.include_router(estadisticas_router, prefix="/api/v1/estadisticas", tags=["estadisticas"])

# Router de uploads (Cloudinary)
app.include_router(uploads_router)


@app.get("/", tags=["health"])
def root():
    return {
        "message": "Food Store API is running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
