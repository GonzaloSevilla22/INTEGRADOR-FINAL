"""Auth Router: autenticación y sesión."""

from datetime import timedelta

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.core.database import get_session
from app.modules.usuarios.auth_service import AuthService
from app.modules.usuarios.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UsuarioCreate,
    UsuarioPublic,
    CurrentUser,
)

router = APIRouter()


def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    """Dependency para obtener el AuthService."""
    return AuthService(session)


@router.post("/register", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED)
def register(
    data: UsuarioCreate,
    svc: AuthService = Depends(get_auth_service),
) -> UsuarioPublic:
    """
    Registrar nuevo usuario.
    
    Parámetros:
    - **nombre**: Nombre del usuario
    - **apellido**: Apellido del usuario
    - **email**: Email único
    - **celular**: Teléfono (opcional)
    - **password**: Contraseña (mínimo 8 caracteres)
    
    Retorna el usuario creado.
    """
    return svc.register(data)


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Autenticar usuario y obtener JWT token.
    
    El token se devuelve de dos formas:
    1. En la respuesta JSON (acceso_token)
    2. En una cookie httponly (para usar automáticamente en requests posteriores)
    
    Parámetros:
    - **email**: Email del usuario
    - **password**: Contraseña
    
    Retorna:
    - **access_token**: JWT token para usar en Authorization header (o usará la cookie)
    - **token_type**: Tipo de token (Bearer)
    - **usuario**: Información del usuario autenticado
    """
    token_response = svc.login(data)

    cookie_max_age = int(timedelta(hours=24).total_seconds())
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token_response.access_token,
        max_age=cookie_max_age,
        expires=cookie_max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    return token_response


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Renovar access token usando refresh token.
    """
    return svc.refresh(data.refresh_token)


@router.get("/me", response_model=CurrentUser)
def get_me(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    """
    Obtener información del usuario autenticado.
    
    Requiere autenticación por:
    - Cookie httponly (automática después del login)
    - O Authorization header con JWT token válido
    
    Ejemplo:
    ```
    GET /auth/me
    (cookie se envía automáticamente)
    
    O alternamente:
    GET /auth/me
    Authorization: Bearer eyJhbGc...
    ```
    
    Retorna información del usuario actual incluyendo sus roles.
    """
    return current_user


@router.post("/logout")
def logout(response: Response) -> dict:
    """
    Limpiar la sesión eliminando la cookie httponly.
    
    Retorna:
    - **message**: Confirmación de logout
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return {"message": "Sesión cerrada correctamente"}

