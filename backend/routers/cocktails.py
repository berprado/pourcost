from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from database import get_db
from models.cocktail import Cocktail, CocktailDetail, Ingredient, PourCostResult
from services.cogs_calculator import calcular_pourcost
from routers.auth import get_current_user

router = APIRouter(prefix="/cocktails", tags=["cocktails"])


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
    opcionales = [dict(r) for r in rows if r["tipo_parte_combo"] == "OPCIONAL"]

    return CocktailDetail(
        id_combo_coctel=base["id_combo_coctel"],
        nombre_combo=base["nombre_combo"],
        descripcion_combo=base["descripcion_combo"],
        nombre_categoria_combo=base["nombre_categoria_combo"],
        precio_venta=float(base["precio_venta"]) if base["precio_venta"] else None,
        principales=[Ingredient(**{k: (float(v) if k in ("cantidad_receta","wac_actual","unidades_detalle_por_base","cantidad_unidad_base","cogs_ingrediente") else v) for k, v in r.items() if k in Ingredient.model_fields}) for r in principales],
        opcionales=[Ingredient(**{k: (float(v) if k in ("cantidad_receta","wac_actual","unidades_detalle_por_base","cantidad_unidad_base","cogs_ingrediente") else v) for k, v in r.items() if k in Ingredient.model_fields}) for r in opcionales],
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
    opcionales = [dict(r) for r in rows if r["tipo_parte_combo"] == "OPCIONAL"]

    opcional_elegido = None
    if opcionales:
        matches = [o for o in opcionales if o["id_producto"] == optional_id]
        if not matches:
            raise HTTPException(status_code=404, detail="Ingrediente opcional no encontrado")
        opcional_elegido = matches[0]

    return calcular_pourcost(
        id_combo=base["id_combo_coctel"],
        nombre_combo=base["nombre_combo"],
        precio_venta=float(base["precio_venta"]) if base["precio_venta"] else None,
        ingredientes_principales=principales,
        ingrediente_opcional=opcional_elegido,
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
