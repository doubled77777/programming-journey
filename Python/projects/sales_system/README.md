# Sales System

Sistema de ventas backend construido con **Python + Flask + SQLite**, con
checkout real integrado a **Mercado Pago** (Checkout API vía Orders).
Proyecto de portafolio orientado a demostrar buenas prácticas de backend:
validación, manejo de errores, transacciones, concurrencia, idempotencia,
autenticación/autorización, logging y testing — no solo un CRUD.

## Tabla de contenidos

- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración (`.env`)](#configuración-env)
- [Crear la base de datos](#crear-la-base-de-datos)
- [Ejecutar el proyecto](#ejecutar-el-proyecto)
- [Endpoints](#endpoints)
- [Probar el checkout con Mercado Pago](#probar-el-checkout-con-mercado-pago)
- [Tests automatizados](#tests-automatizados)
- [Decisiones técnicas importantes](#decisiones-técnicas-importantes)
- [Limitaciones conocidas](#limitaciones-conocidas)

## Tecnologías

- Python 3
- Flask
- SQLite
- HTML / CSS / JavaScript (frontend simple, sin frameworks)
- Mercado Pago (Card Payment Brick + Checkout API vía Orders)
- pytest (testing)

Deliberadamente **no** se usan frameworks ORM, colas de mensajes, Docker,
ni bases de datos distintas a SQLite: para el tamaño y objetivo de este
proyecto, no aportan un problema real que resolver — se prioriza que Python
+ Flask + SQLite sea suficiente y bien usado antes que sumar tecnología.

## Estructura del proyecto

```text
sales_system/
├── app.py                      # Rutas de la API (Flask)
├── config.py                   # Configuración centralizada (lee .env)
├── db.py                       # Conexión a SQLite
├── repository.py               # Acceso a datos y reglas de negocio (productos, ventas)
├── auth.py                     # Autenticación/autorización de rutas admin
├── logging_config.py           # Configuración de logging
├── services/
│   └── mercadopago_service.py  # Integración con Mercado Pago (Orders API)
├── database/
│   ├── create_database.py      # Crea/migra el esquema de la base de datos
│   └── sales.db                # Base de datos SQLite (incluye datos de ejemplo)
├── frontend/
│   └── index.html              # Checkout (selección de producto + Card Payment Brick)
├── tests/
│   ├── conftest.py             # Fixtures de pytest (BD temporal por test)
│   └── test_app.py             # Suite de tests
├── experiments/                # Scripts de aprendizaje previos (ver experiments/README.md)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Instalación

```bash
git clone <url-del-repositorio>
cd sales_system

python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Configuración (`.env`)

Copia el archivo de ejemplo y complétalo:

```bash
cp .env.example .env
```

Variables:

| Variable | Descripción |
|---|---|
| `MERCADOPAGO_ACCESS_TOKEN` | Access Token de Mercado Pago. Usa el de **prueba** mientras desarrollas (se obtiene en *Tus integraciones → tu aplicación → Credenciales de prueba*) |
| `ADMIN_API_KEY` | Clave para las rutas administrativas. Genera una propia: `python -c "import secrets; print(secrets.token_hex(24))"` |
| `FLASK_DEBUG` | `true` en desarrollo, `false` en producción |
| `FLASK_PORT` | Puerto donde corre Flask (por defecto `5000`) |
| `CORS_ORIGINS` | `*` en desarrollo; en producción, el dominio real (ej. `https://mi-tienda.com`) |
| `MERCADOPAGO_TIMEOUT` | Segundos máximos de espera al llamar a Mercado Pago (por defecto `10`) |

**Nunca subas tu `.env` real a un repositorio** — ya está en `.gitignore`.

## Crear la base de datos

```bash
python database/create_database.py
```

Este script es seguro de ejecutar varias veces: si la base de datos no
existe, la crea desde cero (con productos de ejemplo); si ya existe, solo
agrega las columnas o índices que falten, sin borrar datos.

## Ejecutar el proyecto

**Backend:**

```bash
python app.py
```

Por defecto queda disponible en `http://127.0.0.1:5000`.

**Frontend:** abre `frontend/index.html` directamente en el navegador (doble
clic, o "Abrir con" tu navegador). No necesita un servidor web propio — habla
con el backend en `http://localhost:5000` vía `fetch`.

## Endpoints

### Públicos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Estado del servidor |
| `GET` | `/productos` | Lista todos los productos |
| `GET` | `/productos/<id>` | Detalle de un producto |
| `POST` | `/process_order` | Procesa una compra (cobra con Mercado Pago y registra la venta) |

**Ejemplo `POST /process_order`:**

```bash
curl -X POST http://127.0.0.1:5000/process_order \
  -H "Content-Type: application/json" \
  -d '{
        "producto_id": 1,
        "cantidad": 2,
        "token": "<token generado por el Card Payment Brick>",
        "payment_method_id": "visa",
        "installments": 1,
        "payer": {"email": "comprador@test.com"},
        "client_request_id": "un-identificador-unico-por-intento-de-compra"
      }'
```

`client_request_id` es obligatorio y debe ser único por cada intento de
compra (el frontend lo genera automáticamente) — es la clave de la
idempotencia: si el mismo request se reintenta, el backend no vuelve a
cobrar ni a registrar una segunda venta.

Respuestas posibles: `200` (éxito), `400` (datos inválidos o stock
insuficiente), `402` (pago rechazado), `404` (producto inexistente), `409`
(pago aprobado pero no se pudo completar el pedido — requiere contactar
soporte con la referencia dada), `502` (no se pudo contactar a Mercado
Pago).

### Administrativas (requieren header `X-API-Key`)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/productos` | Crea un producto |
| `PUT` | `/productos/<id>` | Actualiza un producto (parcial) |
| `DELETE` | `/productos/<id>` | Elimina un producto |
| `GET` | `/ventas` | Lista todas las ventas registradas |

**Ejemplo:**

```bash
curl -X POST http://127.0.0.1:5000/productos \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <tu ADMIN_API_KEY>" \
  -d '{"nombre": "Monitor", "precio": 500, "stock": 10}'
```

## Probar el checkout con Mercado Pago

Con credenciales de **prueba**, usa estas tarjetas oficiales (Perú):

| Tipo | Número | CVV | Vencimiento |
|---|---|---|---|
| Visa (crédito) | `4009 1753 3280 6176` | `123` | `11/30` |
| Mastercard (crédito) | `5031 7557 3453 0604` | `123` | `11/30` |

El **resultado del pago** lo decide el nombre del titular que escribas, no
la tarjeta:

| Nombre del titular | Resultado |
|---|---|
| `APRO` | Pago aprobado |
| `OTHE` | Rechazado (error general) |
| `FUND` | Rechazado (fondos insuficientes) |
| `SECU` | Rechazado (CVV inválido) |

## Tests automatizados

```bash
python -m pytest tests/ -v
```

Cada test corre contra una base de datos SQLite **temporal y aislada**
(nunca contra `database/sales.db`), y **nunca hace una llamada real a
Mercado Pago** — la integración se reemplaza por un mock, así los tests son
rápidos, repetibles y no generan cargos ni dependen de que Mercado Pago esté
disponible.

Cobertura actual (20 tests):
- Listado y consulta de productos.
- Venta exitosa (pago aprobado): registra venta y descuenta stock.
- Validación: cantidad cero, negativa, tipo incorrecto, campos faltantes,
  cuerpo no-JSON.
- Producto inexistente, stock insuficiente.
- Pago rechazado: no registra venta ni descuenta stock.
- Error de red/timeout con Mercado Pago: no registra venta.
- Solicitud duplicada (mismo `client_request_id`): no cobra ni registra dos
  veces.
- Autenticación/autorización de rutas administrativas.
- CRUD de productos como administrador, con validación de datos inválidos.
- **Concurrencia:** 5 hilos compitiendo por la última unidad de un producto
  con `stock = 1` — se verifica que exactamente una compra tenga éxito y el
  stock final sea `0`, nunca negativo ni vendido más de una vez.

## Decisiones técnicas importantes

**Mercado Pago: Orders API, no Payments API.** La integración usa
`POST /v1/orders` en vez de la clásica `POST /v1/payments`. Se intentó
primero con Payments API y falló con `401 Unauthorized use of live
credentials` incluso con credenciales de prueba correctas — la causa real
era que la aplicación de Mercado Pago estaba configurada bajo el modelo
"vía Orders" (marcado como recomendado en la documentación oficial;
Payments API está marcada como legado). El detalle completo de este
diagnóstico está en `experiments/mercadopago_orders_experimento.py` y su
comentario en `experiments/README.md`.

**Concurrencia (stock nunca se vende de más).** El descuento de stock no se
hace con un `SELECT` seguido de un `UPDATE` (eso deja una ventana donde dos
compras simultáneas pueden leer el mismo stock "viejo"). Se hace con una
única sentencia:

```sql
UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?
```

Si `rowcount` es `0`, no había stock suficiente en ese instante exacto —
sin importar cuántas requests lleguen al mismo tiempo. Ver el comentario
extenso en `repository.registrar_venta_y_descontar_stock` y el test
`test_concurrencia_nunca_vende_mas_stock_del_disponible`.

**Transacciones.** El descuento de stock y el registro de la venta ocurren
dentro de una misma transacción SQLite (`BEGIN IMMEDIATE` / `COMMIT` /
`ROLLBACK` explícitos) — o se hacen los dos, o ninguno.

**Consistencia pago-externo ↔ base de datos.** Mercado Pago y SQLite son dos
sistemas independientes; no existe una operación atómica que abarque a
ambos. Si el pago se aprueba pero la escritura en SQLite falla (por
ejemplo, porque el stock se agotó por una venta concurrente justo en ese
instante), el sistema no lo oculta: registra un log `CRITICAL` con el
`order_id` de Mercado Pago y todos los datos necesarios para investigar
manualmente, y le responde al cliente con un mensaje honesto ("tu pago fue
procesado, contáctanos con esta referencia") en vez de un error genérico.

**Idempotencia.** Cada intento de compra lleva un `client_request_id`
generado por el frontend (uno por clic en "Continuar al pago", reutilizado
si el mismo intento se reintenta). El backend lo usa en tres niveles: (1)
antes de cobrar, revisa si ya existe una venta con ese id y si es así
devuelve el resultado ya registrado sin volver a cobrar; (2) lo envía a
Mercado Pago como `X-Idempotency-Key`, para que ni Mercado Pago cobre dos
veces si el request se reintenta ahí; (3) una restricción `UNIQUE` en la
base de datos actúa como última línea de defensa si dos requests
idénticos llegan casi exactamente al mismo tiempo.

**Autenticación/autorización.** Se usa una API key compartida (header
`X-API-Key`) para las rutas administrativas, en vez de un sistema completo
de usuarios con contraseñas — no hay múltiples administradores con cuentas
propias, así que un sistema de login sería complejidad sin beneficio real
hoy. Si el proyecto creciera para necesitar varios administradores, el
paso natural sería migrar a JWT o a una tabla de usuarios con contraseñas
hasheadas.

## Limitaciones conocidas

Estas son omisiones deliberadas, no descuidos — se documentan para que
quede claro qué se decidió no hacer y por qué:

- **Reembolso automático:** si un pago se aprueba pero el pedido no se
  puede completar (caso extremo de la sección de consistencia arriba), el
  sistema no llama automáticamente a la API de reembolsos de Mercado Pago
  — solo lo deja registrado para revisión manual. Automatizarlo es posible
  pero se consideró fuera del alcance de este proyecto.
- **`reporte_automatico.py`** (en `experiments/`) no está conectado a la
  API web — sigue siendo un script de línea de comandos independiente.
- **Sin paginación** en `GET /productos` — el catálogo actual es pequeño;
  el patrón para agregarla (`?page=&per_page=`) es directo de sumar cuando
  haga falta.
- **Montos como `float`:** el proyecto usa `REAL` en SQLite para precios y
  totales. Para un sistema con volúmenes de dinero mayores, sería más
  robusto trabajar en centavos (enteros) o con `Decimal`, para evitar
  errores de redondeo de punto flotante.
- **Servidor de desarrollo de Flask:** `app.run()` no está pensado para
  producción. Un despliegue real necesitaría un servidor WSGI como
  Gunicorn detrás de un proxy (Nginx).
