# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).

---

## [0.1.0] — 2026-02-24

Primera versión funcional. Cubre la **Fase 1** completa: flujo de drill-down desde login hasta visualización de pour cost.

### Agregado

#### Infraestructura y configuración
- `.mcp.json` en la raíz del proyecto — configuración MCP MySQL para consultas directas desde Claude Code (solución al bug de path mismatch con `claude mcp add` en Windows)
- `.gitignore` — excluye `venv/`, `__pycache__/`, `.env`, `node_modules/`
- `backend/.env` — variables de entorno para DB, JWT y almacén activo

#### Base de datos (MySQL 5.6)
- Vista `vw_pourcost_receta` — une `vw_combo_detalle_reload`, `vw_cache_wac_producto_detalle` (id_almacen=1) y `vw_menubackstage` (tipo='combo', id_dia=1). Calcula `cantidad_unidad_base` y `cogs_ingrediente` por ingrediente. Compatible con MySQL 5.6 (sin CTEs ni funciones de ventana)
- Tabla `app_cocktail` — preparada para Fase 3 (cócteles propios de la app)
- Tabla `app_cocktail_detalle` — preparada para Fase 3

#### Backend (FastAPI)
- `config.py` — carga `.env` con `python-dotenv`, expone `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_HOURS`, `ID_ALMACEN`
- `database.py` — engine async SQLAlchemy + aiomysql, `charset=latin1` en la URL para compatibilidad con la DB del POS
- `services/auth_service.py` — `hash_password()` (SHA-256), `verify_password()`, `create_token()` y `decode_token()` con `python-jose`
- `services/cogs_calculator.py` — `calcular_pourcost()`: recibe listas de ingredientes (principal + opcional elegido), devuelve `PourCostResult` con `cogs_total`, `margen`, `pour_cost` e indicador `incompleto`
- `routers/auth.py` — `POST /auth/login` (valida SHA-256 contra `seg_usuario`, `estado='HAB'`, `habilitado=1`) y `GET /auth/me`
- `routers/cocktails.py` — `GET /cocktails`, `GET /cocktails/categories`, `GET /cocktails/{id}` (split principal/opcional), `GET /cocktails/{id}/pourcost`, `GET /cocktails/{id}/pourcost/{optional_id}`
- `routers/products.py` — `GET /products`, `GET /products/no-wac`, `GET /products/{id}/wac`
- `main.py` — app FastAPI con CORS abierto (`allow_origins=["*"]`), health check en `GET /`

#### Frontend (Vue 3 CDN)
- `index.html` — shell HTML con tema oscuro BackStage, CSS completo embebido, carga Vue 3 desde unpkg CDN, favicon
- `api.js` — fetch wrapper con token Bearer en memoria (`window._token`, nunca localStorage), reload automático en 401. Locale Bolivia (`es-BO`): `fmtBs(v)` → `"Bs 1.234,56"`, `fmtPct(v)` → `"32,3%"`, expuestos en `window`
- `app.js` — root component Vue con template definido como string JS (solución al bug de self-closing tags), máquina de estados: `list` → `detail` → `pourcost`
- `LoginForm.js` — POST login + GET me, emite `logged-in` con token y datos del usuario
- `CocktailList.js` — tabla con búsqueda por nombre/código y filtro por categoría. Precio en formato Boliviano
- `CocktailDetail.js` — ingredientes principales y selector de opcionales (bloqueado hasta selección si hay opcionales). Precio en formato Boliviano
- `PourCostPanel.js` — tabla COGS por ingrediente con fracción de unidad base (4 decimales, locale `es-BO`); KPIs: COGS total, margen, utilidad%, pour cost con badge de color (verde < 28%, amarillo < 38%, rojo ≥ 38%); alerta visual si COGS incompleto
- `assets/icons/` — favicon e íconos en todos los tamaños requeridos para PWA (preparados para Fase 4)

### Corregido

- **Vue compiler-30 (SyntaxError en mount)**: los custom elements con self-closing tag (`<cocktail-list ... />`) en un template HTML inline son ignorados por el parser del navegador — el `/>` se trata como tag abierto, haciendo que `v-else-if` quede anidado dentro del `v-if` en lugar de ser su hermano. Solución: mover el template del root component a `app.js` como template string JS, donde Vue lo parsea directamente sin interferencia del parser HTML.

### Decisiones técnicas documentadas

- `tipo_parte_combo` en `vw_combo_detalle_reload` es MAYÚSCULAS: `'PRINCIPAL'` / `'OPCIONAL'` (difiere del CLAUDE.md inicial)
- MCP MySQL (`@benborla29/mcp-server-mysql`) es read-only para DDL — los objetos de DB se crean con `mysql.exe --default-character-set=latin1`
- Colisión de charset entre MCP (`cp850`) y la DB (`latin1_swedish_ci`): evitar comparaciones de strings en queries via MCP; usar identificadores numéricos
- El servidor uvicorn se lanza con `start cmd /k` para mantener el proceso vivo en Windows tras cerrar la sesión de Claude Code

---

*PourCost App — BackStage Bar — Uso interno*
