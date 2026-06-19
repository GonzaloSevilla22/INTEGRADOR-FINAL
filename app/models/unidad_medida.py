from typing import Optional

from sqlmodel import Field

from app.core.base import BaseModel


class UnidadMedida(BaseModel, table=True):
    __tablename__ = "unidades_medida"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, nullable=False, unique=True)
    simbolo: str = Field(max_length=10, nullable=False)
    tipo: str = Field(max_length=50, nullable=False)
