from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from database import get_db
from models.cocktail import Cocktail, CocktailDetail, Ingredient, PourCostResult
from services.cogs_calculator import calcular_pourcost
from routers.auth import get_current_user

router = APIRouter(prefix="/cocktails", tags=["cocktails"])

# Campos numéricos que deben convertirse explícitamente desde Decimal/string de MySQL
_FLOAT_FIELDS = {
    "cantidad_receta",
    "wac_actual",
    "unidades_detalle_por_base",
    "cantidad_unidad_base",
    "cogs_ingrediente",
    "medida_unidad_base",
}


def row_to_ingredient(r: dict) -> Ingredient:
    """Convierte una fila de vw_pourcost_receta a un objeto Ingredient."""
    return Ingredient(
        id_producto=r["id_producto"],
        nombre_producto=r["nombre_producto"],
        nombre_categoria_producto=r["nombre_categoria_producto"],
        cantidad_receta=float(r["cantidad_receta"]),
        tipo_cantidad_combo=r["tipo_cantidad_combo"],
        tipo_parte_combo=r["tipo_parte_combo"],
        unidad_base=r["unidad_base"],
        medida_unidad_base=float(r["medida_unidad_base"]) if r.get("medida_unidad_base") is not None else None,
        unidades_detalle_por_base=float(r["unidades_detalle_por_base"]),
        unidad_detalle=r["unidad_detalle"],
        wac_actual=float(r["wac_actual"]),
        sin_wac=r["sin_wac"],
        cantidad_unidad_base=float(r["cantidad_unidad_base"]),
        cogs_ingrediente=float(r["cogs_ingrediente"]),
    )


@router.get("", response_model=List[Cocktail])
async def list_cocktails(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT id_combo_coctel, codigo_combo, nombre_combo, descripcion_combo,
               nombre_categoria_combo, precio_venta
        FROM vw_pourcost_receta
        GROUP BY id_combo_coctel, codigo_combo, nombre_combo, descripcion_combo,
                 nombre_categoria_combo, precio_venta
        ORDER BY nombre_categoria_combo, nombre_combo
    """))
    return [dict(r) for r in result.mappings()]


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT DISTINCT nombre_categoria_combo
        FROM vw_pourcost_receta
        ORDER BY nombre_categoria_combo
    """))
    return [r[0] for r in result]


@router.get("/{id}", response_model=CocktailDetail)
async def get_cocktail(id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        text("SELECT * FROM vw_pourcost_receta WHERE id_combo_coctel = :id"),
        {"id": id},
    )
    rows = result.mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Cóctel no encontrado")

    base = rows[0]
    principales = [dict(r) for r in rows if r["tipo_parte_combo"] == "PRINCIPAL"]
    opcionales  = [dict(r) for r in rows if r["tipo_parte_combo"] == "OPCIONAL"]

    return CocktailDetail(
        id_combo_coctel=base["id_combo_coctel"],
        nombre_combo=base["nombre_combo"],
        descripcion_combo=base["descripcion_combo"],
        nombre_categoria_combo=base["nombre_categoria_combo"],
        precio_venta=float(base["precio_venta"]) if base["precio_venta"] else None,
        principales=[row_to_ingredient(r) for r in principales],
        opcionales=[row_to_ingredient(r) for r in opcionales],
    )


@router.get("/{id}/pourcost/{optional_id}", response_model=PourCostResult)
async def get_pourcost(
    id: int,
    optional_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM vw_pourcost_receta WHERE id_combo_coctel = :id"),
        {"id": id},
    )
    rows = result.mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Cóctel no encontrado")

    base = rows[0]
    principales = [dict(r) for r in rows if r["tipo_parte_combo"] == "PRINCIPAL"]
    opcionales  = [dict(r) for r in rows if r["tipo_parte_combo"] == "OPCIONAL"]

    matches = [o for o in opcionales if o["id_producto"] == optional_id]
    if not matches:
        raise HTTPException(status_code=404, detail="Ingrediente opcional no encontrado")

    return calcular_pourcost(
        id_combo=base["id_combo_coctel"],
        nombre_combo=base["nombre_combo"],
        precio_venta=float(base["precio_venta"]) if base["precio_venta"] else None,
        ingredientes_principales=principales,
        ingrediente_opcional=matches[0],
    )


@router.get("/{id}/pourcost", response_model=PourCostResult)
async def get_pourcost_sin_opcional(
    id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM vw_pourcost_receta WHERE id_combo_coctel = :id"),
        {"id": id},
    )
    rows = result.mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Cóctel no encontrado")

    base = rows[0]
    principales = [dict(r) for r in rows if r["tipo_parte_combo"] == "PRINCIPAL"]

    return calcular_pourcost(
        id_combo=base["id_combo_coctel"],
        nombre_combo=base["nombre_combo"],
        precio_venta=float(base["precio_venta"]) if base["precio_venta"] else None,
        ingredientes_principales=principales,
    )
