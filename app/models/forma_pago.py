from typing import Optional

from sqlmodel import Field

from app.core.base import BaseModel


class FormaPago(BaseModel, table=True):
    __tablename__ = "formas_pago"

    codigo: str = Field(primary_key=True, max_length=50, nullable=False)
    nombre: str = Field(max_length=100, nullable=False, unique=True)
    descripcion: Optional[str] = Field(default=None, nullable=True)
