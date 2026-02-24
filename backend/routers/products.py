from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from database import get_db
from models.product import Product, WACDetail
from routers.auth import get_current_user
from config import ID_ALMACEN

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[Product])
async def list_products(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT
            w.id_producto,
            w.nombre_producto,
            w.nombre_categoria,
            w.wac_actual,
            0 AS sin_wac,
            w.fecha_actualizacion
        FROM vw_cache_wac_producto_detalle w
        WHERE w.id_almacen = :almacen
        UNION ALL
        SELECT
            p.id AS id_producto,
            p.nombre AS nombre_producto,
            'Sin categoría' AS nombre_categoria,
            NULL AS wac_actual,
            1 AS sin_wac,
            NULL AS fecha_actualizacion
        FROM vw_productos_sin_costo_cache p
        ORDER BY nombre_producto
    """), {"almacen": ID_ALMACEN})
    return [dict(r) for r in result.mappings()]


@router.get("/no-wac", response_model=List[Product])
async def list_no_wac(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT
            p.id AS id_producto,
            p.nombre AS nombre_producto,
            'Sin categoría' AS nombre_categoria,
            NULL AS wac_actual,
            1 AS sin_wac,
            NULL AS fecha_actualizacion
        FROM vw_productos_sin_costo_cache p
        ORDER BY p.nombre
    """))
    return [dict(r) for r in result.mappings()]


@router.get("/{id}/wac", response_model=WACDetail)
async def get_wac(id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        text("""
            SELECT id_producto, nombre_producto, wac_actual, fecha_actualizacion
            FROM vw_cache_wac_producto_detalle
            WHERE id_producto = :id AND id_almacen = :almacen
        """),
        {"id": id, "almacen": ID_ALMACEN},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Producto sin WAC registrado")
    return dict(row)
