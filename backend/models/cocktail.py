from pydantic import BaseModel
from typing import List, Optional


class Cocktail(BaseModel):
    id_combo_coctel: int
    codigo_combo: str
    nombre_combo: str
    descripcion_combo: Optional[str]
    nombre_categoria_combo: str
    precio_venta: Optional[float]


class Ingredient(BaseModel):
    id_producto: int
    nombre_producto: str
    nombre_categoria_producto: str
    cantidad_receta: float
    tipo_cantidad_combo: str
    tipo_parte_combo: str
    unidad_base: str
    unidades_detalle_por_base: float
    unidad_detalle: str
    wac_actual: float
    sin_wac: int
    cantidad_unidad_base: float
    cogs_ingrediente: float


class CocktailDetail(BaseModel):
    id_combo_coctel: int
    nombre_combo: str
    descripcion_combo: Optional[str]
    nombre_categoria_combo: str
    precio_venta: Optional[float]
    principales: List[Ingredient]
    opcionales: List[Ingredient]


class IngredientPourCost(BaseModel):
    id_producto: int
    nombre_producto: str
    cantidad_receta: float
    unidad_detalle: str
    wac_actual: float
    cantidad_unidad_base: float
    cogs_ingrediente: float
    sin_wac: int


class PourCostResult(BaseModel):
    id_combo_coctel: int
    nombre_combo: str
    precio_venta: Optional[float]
    ingredientes: List[IngredientPourCost]
    cogs_total: Optional[float]
    margen: Optional[float]
    pour_cost: Optional[float]
    incompleto: bool
