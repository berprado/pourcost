from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Product(BaseModel):
    id_producto: int
    nombre_producto: str
    nombre_categoria: str
    wac_actual: Optional[float]
    sin_wac: int
    fecha_actualizacion: Optional[datetime]


class WACDetail(BaseModel):
    id_producto: int
    nombre_producto: str
    wac_actual: Optional[float]
    fecha_actualizacion: Optional[datetime]
