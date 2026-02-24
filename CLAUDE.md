# PourCost App — BackStage Bar
> **Instrucciones para Claude Code**  
> Motor COGS V9 | FastAPI + Vue 3 + MySQL | Base de datos: `adminerp`

---

## ¿Qué es este proyecto?

Aplicación web interna para **BackStage Bar** que calcula, visualiza y simula el **pour cost** de los cócteles del menú. Se integra de forma **no invasiva** con el sistema POS BackApp2026: solo lee desde vistas y tablas existentes, nunca modifica la estructura operativa del POS.

---

## Regla fundamental — NO INVASIVIDAD

> ⚠️ **CRÍTICO**: La app opera en modo **lectura** sobre todas las tablas y vistas del POS.  
> Las únicas escrituras permitidas son sobre tablas con prefijo `app_` creadas exclusivamente para esta app.  
> **Nunca** escribir en tablas originales del POS.

---

## Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| Base de datos | MySQL — `adminerp` | Sistema existente. Solo lectura en tablas POS. |
| Backend | FastAPI (Python) | Async. SQLAlchemy + `aiomysql`. |
| Frontend | Vue 3 via CDN | Sin build tools. SPA en archivos `.js` planos. |
| Auth | JWT + SHA-256 | Valida contra `seg_usuario` del POS. |
| Almacenamiento app | Tablas `app_*` en `adminerp` | Solo para cócteles creados en app. |

---

## Contexto del negocio — Motor COGS V9

### Conceptos clave

- **Producto**: entidad inventariable en `alm_producto`. Tiene stock, costo y unidad de medida.
- **Unidad base**: unidad física completa que se compra (botella, lata). El WAC siempre se expresa en unidad base.
- **Unidad detalle**: fracción en que se divide la unidad base para recetas (Oz, ml). Ejemplo: 1 botella Tequila 750ml = 25 Oz.
- **Producto comandable**: se vende completo, sin fraccionarse (Corona, Red Bull). Consume 1 unidad base por unidad vendida.
- **Combo/Cóctel**: producto vendible definido en `bar_combo_coctel`. Tiene una receta con ingredientes.
- **Receta**: definida en `bar_detalle_combo_bar`. Lista ingredientes, cantidades y tipo (principal/opcional).
- **Ingrediente principal**: obligatorio en la receta. Siempre se consume.
- **Ingrediente opcional**: el cliente elige uno entre las opciones disponibles. Solo se consume el elegido.
- **WAC**: Weighted Average Cost. Se recalcula automáticamente vía trigger en cada ingreso al almacén. Se almacena en `cache_wac_producto`. Siempre en unidad base.

### Fórmula de cálculo

```
fracción_unidad_base  = cantidad_oz / cantidad_detalle_por_unidad
cogs_ingrediente      = fracción_unidad_base × WAC_actual
cogs_cóctel           = Σ cogs_ingrediente (principal + opcional elegido)
margen                = precio_venta - cogs_cóctel
pour_cost             = cogs_cóctel / precio_venta
```

**Ejemplo — Jagerbomb:**
```
Jager 1.5 Oz (botella 33 Oz, WAC=240 Bs): 1.5/33 × 240 = 10.91 Bs
Red Bull 1 lata (comandable, WAC=8 Bs):   1 × 8 = 8 Bs
COGS total: 18.91 Bs | Precio: 40 Bs | Pour Cost: 47.3%
```

### Casos especiales

- **Ingrediente sin WAC** (`wac_actual = NULL` o `0`): el producto ingresó como bonificación (costo 0). No figura en `cache_wac_producto`. Existe en `vw_productos_sin_costo_cache`. El COGS del cóctel debe marcarse como **"Incompleto"** — nunca mostrar un número incorrecto.
- **Almacén activo**: `id_almacen = 1`. Hardcodeado en esta versión, parametrizable en `config.py` para versiones futuras.
- **Barra activa**: `id_barra = 1`.

---

## Fuentes de datos — Vistas del POS (solo lectura)

### `vw_combo_detalle_reload`
Recetas completas de todos los combos activos.

Columnas clave:
```
id_combo_coctel, codigo_combo, nombre_combo, descripcion_combo, nombre_categoria_combo
id_producto, codigo_producto, nombre_producto, nombre_categoria_producto
cantidad_combo          -- cantidad definida en receta (en unidad detalle o unidad base)
tipo_cantidad_combo     -- "Unidad" = unidad base completa | "Detalle" = fracción (Oz, ml)
tipo_parte_combo        -- "Principal" | "Opcional"
nombre_unidad_medida    -- unidad base (botella, lata)
cantidad_detalle        -- cuántas unidades detalle tiene 1 unidad base (ej: 33 Oz por botella)
nombre_unidad_medida_detalle -- unidad detalle (Oz, ml)
```

### `vw_cache_wac_producto_detalle`
WAC actual por producto con descripciones.

Columnas clave:
```
id_almacen, id_producto, nombre_producto, nombre_categoria
wac_actual              -- costo por unidad base en Bs
fecha_actualizacion
```

### `vw_menubackstage`
Precios de venta vigentes (día 1 = precio estándar).

Columnas clave:
```
cod_combo_producto, nombre, precio_venta, descripcion
id_categoria, nombre_categoria
tipo                    -- "combo" | "producto"
id_origen               -- id del combo o producto
id_dia                  -- siempre filtrar con id_dia = 1
```

### `vw_productos_sin_costo_cache`
Productos que aún no tienen WAC calculado (bonificaciones, productos nuevos sin costo registrado).

### `seg_usuario`
Tabla de usuarios del POS. Usada solo para autenticación.

Campos relevantes:
```
id, nombres, paterno, materno, usuario, contrasena (SHA-256), estado, habilitado
```

---

## Vista nueva a crear — `vw_pourcost_receta`

> Esta vista debe crearse en `adminerp`. Une las tres fuentes para calcular el pour cost estático por receta.

```sql
CREATE VIEW vw_pourcost_receta AS
SELECT
    det.id_combo_coctel,
    det.codigo_combo,
    det.nombre_combo,
    det.descripcion_combo,
    det.nombre_categoria_combo,
    menu.precio_venta,
    det.id_producto,
    det.codigo_producto,
    det.nombre_producto,
    det.nombre_categoria_producto,
    det.cantidad_combo            AS cantidad_receta,
    det.tipo_cantidad_combo,
    det.tipo_parte_combo,
    det.nombre_unidad_medida      AS unidad_base,
    det.cantidad_detalle          AS unidades_detalle_por_base,
    det.nombre_unidad_medida_detalle AS unidad_detalle,
    COALESCE(wac.wac_actual, 0)   AS wac_actual,
    CASE
        WHEN wac.wac_actual IS NULL THEN 1
        ELSE 0
    END AS sin_wac,
    -- Fracción de unidad base consumida
    CASE
        WHEN det.tipo_cantidad_combo = 'Unidad' THEN det.cantidad_combo
        ELSE det.cantidad_combo / det.cantidad_detalle
    END AS cantidad_unidad_base,
    -- COGS del ingrediente
    CASE
        WHEN det.tipo_cantidad_combo = 'Unidad'
            THEN det.cantidad_combo * COALESCE(wac.wac_actual, 0)
        ELSE (det.cantidad_combo / det.cantidad_detalle) * COALESCE(wac.wac_actual, 0)
    END AS cogs_ingrediente
FROM vw_combo_detalle_reload det
LEFT JOIN vw_cache_wac_producto_detalle wac
    ON wac.id_producto = det.id_producto
    AND wac.id_almacen = 1
LEFT JOIN vw_menubackstage menu
    ON menu.id_origen = det.id_combo_coctel
    AND menu.tipo = 'combo'
    AND menu.id_dia = 1;
```

---

## Tablas nuevas de la app

Solo estas tablas se crean y escriben desde la app:

### `app_cocktail`
Cócteles creados desde la app (no existen en el POS).
```sql
CREATE TABLE app_cocktail (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(255) NOT NULL,
    descripcion     VARCHAR(500),
    precio_venta    DECIMAL(10,2) NOT NULL,
    id_categoria    INT,
    nombre_categoria VARCHAR(255),
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_id      INT NOT NULL,
    estado          VARCHAR(3) DEFAULT 'HAB'
);
```

### `app_cocktail_detalle`
Ingredientes de los cócteles creados en app.
```sql
CREATE TABLE app_cocktail_detalle (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    id_cocktail     INT NOT NULL,
    id_producto     INT NOT NULL,       -- FK a alm_producto (solo lectura del POS)
    cantidad        DECIMAL(10,4) NOT NULL,
    tipo            VARCHAR(20) NOT NULL,  -- 'Principal' | 'Opcional'
    ind_paq_detalle TINYINT DEFAULT 0,    -- 0=Detalle (Oz), 1=Unidad base completa
    FOREIGN KEY (id_cocktail) REFERENCES app_cocktail(id)
);
```

---

## Autenticación

### Flujo
1. POST `/auth/login` con `{ usuario, contrasena }`
2. Backend hace `SHA256(contrasena_input)` y compara con `seg_usuario.contrasena`
3. Valida `estado = 'HAB'` y `habilitado = 1` — **no validar fechas de vigencia**
4. Si válido: genera JWT con `{ id, nombres, paterno, usuario }` y expiración configurable (default: 8h)
5. Frontend guarda JWT **en memoria** (no `localStorage`, no `sessionStorage`)
6. Cada request incluye `Authorization: Bearer <token>`

### Reglas
```python
# Validación correcta
usuario_activo = (estado == 'HAB') and (habilitado == 1)
hash_match     = hashlib.sha256(password.encode()).hexdigest() == contrasena_bd
```

> **Nota de seguridad**: el POS usa SHA-256 sin salt. Esta limitación viene del POS y no se puede cambiar. En producción usar HTTPS obligatoriamente.

---

## Endpoints de la API

### Auth
| Método | Endpoint | Auth |
|---|---|---|
| POST | `/auth/login` | No |
| GET | `/auth/me` | Sí |

### Cócteles del menú (POS)
| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| GET | `/cocktails` | Lista combos activos con nombre, código, categoría, precio | Sí |
| GET | `/cocktails/categories` | Categorías disponibles para filtrado | Sí |
| GET | `/cocktails/{id}` | Detalle: ingredientes, cantidades, tipo (principal/opcional) | Sí |
| GET | `/cocktails/{id}/pourcost/{optional_id}` | COGS + margen + pour cost para combinación principal + opcional elegido | Sí |

### Productos y WAC
| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| GET | `/products` | Todos los productos con WAC actual. Marca sin_wac=1 si aplica | Sí |
| GET | `/products/no-wac` | Productos sin WAC (bonificaciones/nuevos) | Sí |
| GET | `/products/{id}/wac` | WAC actual de un producto | Sí |

### Simulaciones
| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `/simulate/substitution` | Recibe un `id_producto` sustituto y devuelve su WAC real. El cálculo final ocurre en el frontend. | Sí |

> ⚠️ **No existe `/simulate/express`** — la simulación express es 100% local en Vue. El único endpoint de simulación es `/simulate/substitution`, y su único propósito es devolver el WAC real de un producto sustituto desde la BD.

### Cócteles creados en app
| Método | Endpoint | Auth |
|---|---|---|
| GET | `/app-cocktails` | Sí |
| POST | `/app-cocktails` | Sí |
| PUT | `/app-cocktails/{id}` | Sí |
| DELETE | `/app-cocktails/{id}` | Sí |
| GET | `/app-cocktails/{id}/pourcost` | Sí |

---

## Estructura de archivos del proyecto

```
pourcost-app/
├── CLAUDE.md                        ← este archivo
├── backend/
│   ├── main.py                      # Entry point FastAPI, registro de routers
│   ├── config.py                    # DB URL, JWT secret, expiración, id_almacen=1
│   ├── database.py                  # SQLAlchemy async engine + session
│   ├── models/
│   │   ├── auth.py                  # Pydantic: LoginRequest, TokenResponse, UserMe
│   │   ├── cocktail.py              # Pydantic: Cocktail, Ingredient, PourCostResult
│   │   ├── product.py               # Pydantic: Product, WACDetail
│   │   └── simulation.py            # Pydantic: SimulateExpressRequest, SimulateSubstRequest
│   ├── routers/
│   │   ├── auth.py                  # POST /auth/login, GET /auth/me
│   │   ├── cocktails.py             # GET /cocktails, /cocktails/{id}, /cocktails/{id}/pourcost/{opt}
│   │   ├── products.py              # GET /products, /products/no-wac, /products/{id}/wac
│   │   ├── simulate.py              # POST /simulate/express, /simulate/substitution
│   │   └── app_cocktails.py         # CRUD /app-cocktails
│   ├── services/
│   │   ├── cogs_calculator.py       # Lógica pura de cálculo COGS/margen/pour cost
│   │   └── auth_service.py          # SHA-256, generación y validación JWT
│   └── requirements.txt
└── frontend/
    ├── index.html                   # Shell HTML, carga Vue 3 CDN y scripts
    ├── app.js                       # Instancia Vue, router de vistas, estado global auth
    ├── api.js                       # fetch wrapper con Bearer token automático
    └── components/
        ├── LoginForm.js             # Formulario de autenticación
        ├── CocktailList.js          # Capa 1: lista con búsqueda y filtros
        ├── CocktailDetail.js        # Capa 2: receta, ingredientes, selector de opcional
        ├── PourCostPanel.js         # Capa 3: COGS por ingrediente, margen, pour cost
        ├── SimulatorExpress.js      # Simulación express (edita WAC/cantidades)
        ├── SimulatorSubst.js        # Simulación por sustitución (elige otro producto)
        └── AppCocktailForm.js       # Crear/editar cócteles propios de la app
```

---

## Flujo de navegación — Drill-down por capas

```
[Login]
   ↓
[Capa 1 — Lista de cócteles]
   Muestra: nombre, código, categoría, precio de venta
   Controles: búsqueda por nombre, filtro por categoría, filtro por rango de precio
   Acción: click en un cóctel → Capa 2
   ↓
[Capa 2 — Receta del cóctel]
   Muestra: ingrediente(s) principal(es) con cantidad + unidad
            lista de ingredientes opcionales con cantidad + unidad
   ⚠ Ingrediente sin WAC: mostrar ícono de alerta, no calcular COGS parcial
   Acción: usuario selecciona UN ingrediente opcional → Capa 3
   ↓
[Capa 3 — COGS y Pour Cost]
   Muestra por ingrediente: nombre, cantidad, WAC, fracción unidad base, COGS
   Muestra totales del cóctel: COGS total, precio venta, margen, utilidad, pour cost
   Si algún ingrediente tiene sin_wac=1: mostrar "COGS Incompleto ⚠" en lugar del total
   Botones: [Simular Express] [Simular Sustitución]
```

---

## Módulo de simulación

### Simulación Express — 100% frontend, cero requests al backend

> ⚠️ **ARQUITECTURA CRÍTICA**: La simulación express **nunca llama al backend**. Todo el cálculo ocurre en Vue con los datos que ya están en memoria desde que se cargó el pour cost real.

- **Propósito**: ¿Qué pasa si el WAC de este ingrediente cambia? ¿O si uso menos cantidad?
- **Inputs**: tabla editable con WAC y cantidad por ingrediente (pre-poblada con valores reales del backend)
- **Cálculo**: Vue recalcula COGS/margen/pour cost de forma reactiva en cada cambio — sin debounce, sin fetch, sin POST
- **Fórmula aplicada en frontend**:
  ```js
  // Para cada ingrediente:
  const fraccion = ing.tipo_cantidad_combo === 'Unidad'
    ? ing.cantidad_sim
    : ing.cantidad_sim / ing.unidades_detalle_por_base
  ing.cogs_sim = fraccion * ing.wac_sim

  // Totales reactivos (computed):
  const cogs_total = ingredientes.reduce((s, i) => s + i.cogs_sim, 0)
  const margen     = precio_venta - cogs_total
  const pour_cost  = cogs_total / precio_venta
  ```
- **Permite**: ingresar WAC manual para ingredientes con sin_wac=1 para completar la simulación
- **El endpoint `/simulate/express` NO existe** — fue eliminado de la arquitectura. No crearlo.

### Simulación por Sustitución — POST al backend solo al cambiar ingrediente

- **Propósito**: ¿Qué pasa si cambio este ingrediente por otro producto de la BD?
- **Inputs**: para cada ingrediente, desplegable de productos disponibles en BD (con su WAC real)
- **Flujo**: usuario selecciona producto → POST a `/simulate/substitution` con debounce 400ms → backend devuelve WAC real → Vue recalcula localmente
- **Output**: recalculo reactivo con WAC real del producto elegido — **sin guardar en BD**
- **El POST solo sirve para obtener el WAC del producto sustituto** — el cálculo final sigue siendo local en Vue

---

## Fases de desarrollo

### Fase 1 — Base (arrancar aquí)
1. Crear vista `vw_pourcost_receta` en MySQL
2. Crear tablas `app_cocktail` y `app_cocktail_detalle`
3. Backend: `config.py`, `database.py`, `auth_service.py`, router `/auth`
4. Backend: `cogs_calculator.py`, routers `/cocktails` y `/products`
5. Frontend: `LoginForm.js`, `CocktailList.js`, `CocktailDetail.js`, `PourCostPanel.js`
6. Drill-down completo funcional

### Fase 2 — Simulaciones
1. Frontend: `SimulatorExpress.js` — tabla editable reactiva, cálculo 100% local en Vue, sin requests al backend
2. Backend: `simulate.py` router — único endpoint `POST /simulate/substitution` que devuelve el WAC real de un producto sustituto
3. Frontend: `SimulatorSubst.js` — desplegable de productos, POST al backend solo para obtener WAC, recálculo local
4. Manejo visual completo de ingredientes sin WAC en ambos modos

### Fase 3 — App Cocktails
1. Backend: router `app_cocktails.py` con CRUD completo
2. Frontend: `AppCocktailForm.js`
3. Pour cost de cócteles propios usando WAC reales

### Fase 4 — Extras
1. Exportación PDF/CSV de resultados de simulación
2. Mejoras de UI y filtros avanzados
3. Evaluación de conversión a PWA

---

## Decisiones de diseño

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Vue 3 via CDN | React, Streamlit | Sin build tools. App interna simple. Reactivo para simulaciones. |
| Sin tablas espejo | Tablas espejo + triggers | Los datos del POS se leen en tiempo real. Cero riesgo de desincronización. |
| Sin persistencia de simulaciones (Fase 1) | Guardar en BD | El valor está en el cálculo en tiempo real. PDF/CSV cubre documentar. |
| JWT en memoria | localStorage | Seguridad contra XSS. Suficiente para app interna. |
| Lógica COGS en `cogs_calculator.py` | En SQL / en frontend | Centralizada, testeable, reutilizable para simulaciones. |
| `id_almacen = 1` en `config.py` | Parámetro en cada request | Negocio opera con un almacén. Parametrizable para escalabilidad futura. |

---

## Consideraciones futuras

- **Multi-almacén**: cuando BackStage opere con más almacenes, `id_almacen` debe venir del contexto del JWT o como parámetro de endpoint.
- **Permisos por rol**: extender el JWT con `tipousuario` de `seg_usuario` para diferenciar accesos.
- **WAC histórico**: simular con WAC de una fecha pasada.
- **Persistencia de simulaciones**: tabla `app_simulaciones` para comparación histórica.
- **PWA**: acceso desde móviles del bar sin instalación.

---

## Restricciones MySQL 5.6.12

> ⚠️ **La base de datos corre en MySQL 5.6.12. Respetar estas restricciones en TODAS las consultas.**

### No disponible en 5.6 — nunca usar:
- `WITH ... AS (...)` — CTEs no existen. Usar subqueries o vistas intermedias.
- `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()` — funciones de ventana no existen.
- Columnas tipo `JSON` ni funciones `JSON_*`.
- `LATERAL JOIN`.

### Comportamiento específico de 5.6:
- **`GROUP BY` estricto**: todas las columnas del `SELECT` que no estén dentro de una función de agregación (`SUM`, `COUNT`, `MAX`, etc.) **deben aparecer en el `GROUP BY`**.
- **Charset**: la base usa `latin1_swedish_ci`. Tener cuidado con búsquedas de texto que contengan caracteres especiales (tildes, ñ). Usar `COLLATE` explícito si es necesario.
- **Subqueries en `FROM`**: válidas, son la alternativa a los CTEs. Siempre asignarles un alias.

### Patrón correcto para consultas complejas:

```sql
-- ✅ Correcto en 5.6 — subquery en lugar de CTE
SELECT t.nombre_combo, SUM(t.cogs_ingrediente) AS cogs_total
FROM (
    SELECT nombre_combo, cogs_ingrediente
    FROM vw_pourcost_receta
    WHERE id_combo_coctel = :id
) t
GROUP BY t.nombre_combo;

-- ❌ Incorrecto — CTEs no existen en 5.6
WITH base AS (
    SELECT nombre_combo, cogs_ingrediente FROM vw_pourcost_receta
)
SELECT ...
```

---

## Dependencias Python (requirements.txt)

```
fastapi
uvicorn[standard]
sqlalchemy
aiomysql
python-jose[cryptography]
passlib
pydantic[email]
python-dotenv
```

---

## Variables de entorno (.env)

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=adminerp
JWT_SECRET=cambiar_en_produccion
JWT_EXPIRE_HOURS=8
ID_ALMACEN=1
```

---

*PourCost App — BackStage Bar — Uso interno*
