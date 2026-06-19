from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.deps import get_current_active_user, require_roles
from app.core.database import get_session
from app.core.rbac import ROLE_ADMIN, ROLE_STOCK
from app.modules.usuarios.schemas import CurrentUser
from app.modules.ingredientes.schemas import (
    IngredienteCreate,
    IngredienteDetail,
    IngredienteList,
    IngredientePublic,
    IngredienteUpdate,
)
from app.modules.ingredientes.service import IngredienteService

router = APIRouter()


def get_ingrediente_service(session: Session = Depends(get_session)) -> IngredienteService:
    return IngredienteService(session)


@router.post("", response_model=IngredientePublic, status_code=status.HTTP_201_CREATED)
def create_ingrediente(
    data: IngredienteCreate,
    _: CurrentUser = Depends(require_roles([ROLE_ADMIN, ROLE_STOCK])),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> IngredientePublic:
    return svc.create(data)


@router.get("", response_model=IngredienteList)
def list_ingredientes(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    include_deleted: bool = Query(default=False),
    _: CurrentUser = Depends(get_current_active_user),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> IngredienteList:
    return svc.get_all(offset=offset, limit=limit, include_deleted=include_deleted)


@router.get("/{ingrediente_id}", response_model=IngredientePublic)
def get_ingrediente(
    ingrediente_id: int,
    _: CurrentUser = Depends(get_current_active_user),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> IngredientePublic:
    return svc.get_by_id(ingrediente_id)


@router.get("/{ingrediente_id}/detail", response_model=IngredienteDetail)
def get_ingrediente_detail(
    ingrediente_id: int,
    _: CurrentUser = Depends(get_current_active_user),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> IngredienteDetail:
    return svc.get_detail(ingrediente_id)


@router.patch("/{ingrediente_id}", response_model=IngredientePublic)
async def update_ingrediente(
    ingrediente_id: int,
    data: IngredienteUpdate,
    _: CurrentUser = Depends(require_roles([ROLE_ADMIN, ROLE_STOCK])),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> IngredientePublic:
    return await svc.update(ingrediente_id, data)


@router.delete("/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingrediente(
    ingrediente_id: int,
    _: CurrentUser = Depends(require_roles([ROLE_ADMIN])),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> None:
    svc.soft_delete(ingrediente_id)


@router.patch("/{ingrediente_id}/restore", response_model=IngredientePublic)
def restore_ingrediente(
    ingrediente_id: int,
    _: CurrentUser = Depends(require_roles([ROLE_ADMIN])),
    svc: IngredienteService = Depends(get_ingrediente_service),
) -> IngredientePublic:
    return svc.restore(ingrediente_id)
