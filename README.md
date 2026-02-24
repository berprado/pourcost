# PourCost — BackStage Bar

Aplicación web interna para calcular y visualizar el **pour cost** de los cócteles del menú de BackStage Bar. Se integra de forma **no invasiva** con el sistema POS BackApp2026: solo lee desde vistas y tablas existentes, nunca modifica la estructura operativa del POS.

---

## Stack

| Capa | Tecnología |
|---|---|
| Base de datos | MySQL 5.6 — `adminerp_wac` |
| Backend | FastAPI · SQLAlchemy async · aiomysql |
| Frontend | Vue 3 via CDN (sin build tools) |
| Auth | JWT · SHA-256 (compatible con POS) |

---

## Prerrequisitos

- **WAMP** corriendo con MySQL 5.6 activo
- **Python 3.12+** instalado
- **Node.js** (solo para el MCP de desarrollo, opcional en producción)

---

## Instalación

### 1. Crear entorno virtual e instalar dependencias Python

```cmd
cd c:\wamp\www\pourcost\backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear `backend/.env` (excluido del repositorio por `.gitignore`):

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_contraseña
DB_NAME=adminerp_wac
JWT_SECRET=cambiar_en_produccion
JWT_EXPIRE_HOURS=8
ID_ALMACEN=1
```

### 3. Crear objetos de base de datos

Ejecutar en MySQL los scripts incluidos en `CLAUDE.md` (sección "Vista nueva a crear"):

- **Vista** `vw_pourcost_receta` — une recetas, WAC y precios para calcular COGS
- **Tabla** `app_cocktail` — cócteles creados en la app (Fase 3)
- **Tabla** `app_cocktail_detalle` — ingredientes de los cócteles de la app (Fase 3)

> Usar `mysql.exe --default-character-set=latin1` para evitar colisiones de charset.

---

## Ejecutar

### Backend

```cmd
start cmd /k "cd /d c:\wamp\www\pourcost\backend && venv\Scripts\uvicorn main:app --reload --port 8000"
```

API disponible en `http://localhost:8000`. El servidor se reinicia automáticamente al detectar cambios en el código.

### Frontend

Acceder via WAMP (Apache sirve los archivos estáticos directamente):

```
http://localhost/pourcost/frontend/index.html
```

---

## Uso

1. **Login** con usuario y contraseña del POS (BackApp2026)
2. **Capa 1 — Lista de cócteles**: buscar por nombre o código, filtrar por categoría
3. **Capa 2 — Receta**: ingredientes principales y selector de opcional (requerido si aplica)
4. **Capa 3 — Pour Cost**: COGS por ingrediente, margen, utilidad y pour cost

### Interpretación del pour cost

| Rango | Indicador |
|---|---|
| < 28% | Verde — Óptimo |
| 28% – 38% | Amarillo — Atención |
| > 38% | Rojo — Alto |

### Ingredientes sin WAC

Si un ingrediente no tiene costo registrado (bonificación o producto nuevo), el pour cost del cóctel se marca como **"Incompleto"** y no se muestra un total incorrecto.

---

## Estructura del proyecto

```
pourcost/
├── backend/
│   ├── main.py                  # Entry point FastAPI, CORS, registro de routers
│   ├── config.py                # Variables de entorno y constantes (ID_ALMACEN=1)
│   ├── database.py              # Engine async SQLAlchemy + sesión
│   ├── models/
│   │   ├── auth.py              # LoginRequest, TokenResponse, UserMe
│   │   ├── cocktail.py          # Cocktail, Ingredient, PourCostResult
│   │   └── product.py           # Product, WACDetail
│   ├── routers/
│   │   ├── auth.py              # POST /auth/login · GET /auth/me
│   │   ├── cocktails.py         # GET /cocktails · /cocktails/{id} · /pourcost
│   │   └── products.py          # GET /products · /no-wac · /{id}/wac
│   ├── services/
│   │   ├── auth_service.py      # SHA-256, JWT
│   │   └── cogs_calculator.py   # Lógica COGS/margen/pour cost
│   ├── requirements.txt
│   └── .env                     # ← crear localmente, no en repo
├── frontend/
│   ├── index.html               # Shell HTML, tema oscuro, favicon, CSS
│   ├── api.js                   # Fetch wrapper, token en memoria, fmtBs/fmtPct
│   ├── app.js                   # Root Vue app, navegación por vistas
│   ├── assets/
│   │   └── icons/               # Favicon e íconos PWA (todos los tamaños)
│   └── components/
│       ├── LoginForm.js
│       ├── CocktailList.js
│       ├── CocktailDetail.js
│       └── PourCostPanel.js
├── .mcp.json                    # MCP MySQL para Claude Code
├── CLAUDE.md                    # Instrucciones y contexto para Claude Code
└── README.md                    # Este archivo
```

---

## Notas de diseño

| Decisión | Razón |
|---|---|
| Token JWT en memoria (no localStorage) | Protección XSS. Suficiente para app interna. |
| Vue 3 via CDN, sin build tools | App interna simple. Sin pipeline de compilación. |
| Template root en JS (no HTML inline) | Los custom elements con `/>` en HTML son ignorados por el parser; definirlo en JS evita el error. |
| Locale `es-BO` en `api.js` | Fuente única de formato: `Bs 1.234,56` en toda la app. |
| Solo lectura en tablas del POS | Cero riesgo de desincronización. Integración no invasiva. |
| `id_almacen = 1` en config | Negocio opera con un almacén. Parametrizable en `config.py`. |

---

## Fases de desarrollo

- [x] **Fase 1** — Drill-down completo: Login → Lista → Receta → Pour Cost
- [ ] **Fase 2** — Simulaciones (express y por sustitución de ingredientes)
- [ ] **Fase 3** — Cócteles propios de la app (CRUD + pour cost)
- [ ] **Fase 4** — Exportación PDF/CSV, mejoras UX, evaluación PWA

---

## Seguridad

> El POS usa SHA-256 sin salt. Esta limitación viene del sistema existente y no puede cambiarse.
> **En producción usar HTTPS obligatoriamente.**
