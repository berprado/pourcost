from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from routers import auth, cocktails, products
from database import get_db

app = FastAPI(title="PourCost API — BackStage Bar", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cocktails.router)
app.include_router(products.router)

@app.get("/")
async def root():
    return {"status": "ok", "app": "PourCost API"}

@app.get("/debug/pourcost")
async def debug_pourcost(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM vw_pourcost_receta WHERE id_combo_coctel = 43"))
    rows = result.mappings().all()
    principales = [dict(r) for r in rows if r["tipo_parte_combo"] == "PRINCIPAL"]
    opcionales = [dict(r) for r in rows if r["tipo_parte_combo"] == "OPCIONAL"]
    from services.cogs_calculator import calcular_pourcost
    resultado = calcular_pourcost(
        id_combo=43,
        nombre_combo="TEST",
        precio_venta=380.0,
        ingredientes_principales=principales,
        ingrediente_opcional=opcionales[0] if opcionales else None,
    )
    return resultado.model_dump()