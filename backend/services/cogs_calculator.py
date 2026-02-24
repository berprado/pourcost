from typing import List, Optional
from models.cocktail import IngredientPourCost, PourCostResult


def calcular_pourcost(
    id_combo: int,
    nombre_combo: str,
    precio_venta: Optional[float],
    ingredientes_principales: List[dict],
    ingrediente_opcional: Optional[dict] = None,
) -> PourCostResult:
    """
    Calcula COGS, margen y pour cost para una combinación de ingredientes.
    Los ingredientes vienen como dicts con las columnas de vw_pourcost_receta.
    Si algún ingrediente tiene sin_wac=1, el resultado se marca como incompleto.
    """
    todos = list(ingredientes_principales)
    if ingrediente_opcional:
        todos.append(ingrediente_opcional)

    incompleto = any(ing["sin_wac"] for ing in todos)

    items = [
        IngredientPourCost(
            id_producto=ing["id_producto"],
            nombre_producto=ing["nombre_producto"],
            cantidad_receta=float(ing["cantidad_receta"]),
            tipo_cantidad_combo=ing["tipo_cantidad_combo"],             # NUEVO
            unidad_base=ing["unidad_base"],                             # NUEVO
            medida_unidad_base=float(ing["medida_unidad_base"]) if ing.get("medida_unidad_base") is not None else None,  # NUEVO
            unidad_detalle=ing["unidad_detalle"],
            wac_actual=float(ing["wac_actual"]),
            cantidad_unidad_base=float(ing["cantidad_unidad_base"]),
            cogs_ingrediente=float(ing["cogs_ingrediente"]),
            sin_wac=ing["sin_wac"],
        )
        for ing in todos
    ]

    if incompleto:
        return PourCostResult(
            id_combo_coctel=id_combo,
            nombre_combo=nombre_combo,
            precio_venta=precio_venta,
            ingredientes=items,
            cogs_total=None,
            margen=None,
            pour_cost=None,
            incompleto=True,
        )

    cogs_total = sum(i.cogs_ingrediente for i in items)
    margen = (precio_venta - cogs_total) if precio_venta else None
    pour_cost = (cogs_total / precio_venta) if precio_venta else None

    return PourCostResult(
        id_combo_coctel=id_combo,
        nombre_combo=nombre_combo,
        precio_venta=precio_venta,
        ingredientes=items,
        cogs_total=round(cogs_total, 4),
        margen=round(margen, 4) if margen is not None else None,
        pour_cost=round(pour_cost, 4) if pour_cost is not None else None,
        incompleto=False,
    )
