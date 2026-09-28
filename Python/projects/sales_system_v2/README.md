# Sistema de Ventas — Backend Python (Flask + SQLite)

Proyecto de portfolio para desarrollador backend junior. Sistema de
ventas realista construido con **Python, Flask, SQLite y SQL puro**,
sin pasarela de pagos ni tecnologías externas innecesarias.

Este proyecto es independiente del anterior `sales_system` (que
integraba Mercado Pago); es una implementación nueva, enfocada
exclusivamente en fundamentos sólidos de backend: validación,
transacciones, concurrencia, idempotencia, autenticación/autorización,
seguridad, reportes SQL y testing.

---

## 1. Objetivo

Demostrar conocimientos de backend mediante un sistema de ventas
completo y coherente, priorizando la solidez del backend sobre el
diseño visual del frontend.

## 2. Funcionalidades

- **Productos**: CRUD completo con validación (precio/stock no
  negativos, nombre no vacío) y baja lógica (no se borran físicamente
  porque quedan referenciados en ventas históricas).
- **Clientes**: CRUD con validación y unicidad de email.
- **Usuarios**: gestión de usuarios con contraseña hasheada
  (`werkzeug.security`), nunca en texto plano.
- **Ventas**: registro de una venta con múltiples productos, cálculo
  de subtotales y total **siempre en el backend** (nunca se confía en
  el total que mande el cliente). El precio se copia a
  `detalle_venta` para que cambios futuros de precio no alteren
  ventas históricas.
- **Transacciones**: creación de venta + descuento de stock es una
  única operación atómica (`BEGIN IMMEDIATE` ... `COMMIT`/`ROLLBACK`).
  Si algo falla a mitad de camino, no queda nada a medias.
- **Concurrencia**: el descuento de stock usa un `UPDATE` condicional
  (`WHERE stock >= cantidad`) combinado con el lock de escritura de
  `BEGIN IMMEDIATE`, evitando que dos compras simultáneas vendan más
  stock del disponible. Verificado con un test real usando hilos.
- **Idempotencia**: header opcional `Idempotency-Key` en
  `POST /ventas`; un reintento con la misma clave devuelve la venta ya
  creada en lugar de duplicarla.
- **Autenticación**: login basado en sesión de Flask (cookie firmada),
  contraseñas hasheadas, logout.
- **Autorización**: roles `ADMIN` y `VENDEDOR` con permisos distintos,
  reforzados por decoradores (`@login_required`, `@role_required`).
- **Reportes SQL**: consultas reales con `JOIN`, `GROUP BY`, `SUM`,
  `COUNT`, `ORDER BY` y filtros por fecha.
- **Validación y manejo de errores**: JSON inválido, campos
  faltantes, tipos incorrectos, recursos inexistentes, stock
  insuficiente, credenciales incorrectas, acceso no autorizado, todos
  con códigos HTTP y JSON consistentes.
- **Seguridad**: consultas parametrizadas (sin SQL injection),
  contraseñas hasheadas, secretos vía variables de entorno,
  `password_hash` nunca expuesto en respuestas de la API.
- **Tests automatizados**: 55 tests con `pytest`, incluyendo
  concurrencia real con hilos.
- **Logging**: eventos clave (logins, ventas, errores) sin datos
  sensibles.
- **Frontend simple**: HTML/CSS/JS que consume la API para probar
  todo el flujo (login, armar venta, ver historial, administración).

## 3. Tecnologías

- Python 3.12
- Flask 3.1
- SQLite (vía `sqlite3` de la librería estándar)
- SQL puro (sin ORM, para practicar SQL directamente)
- HTML / CSS / JavaScript (vanilla, sin frameworks)
- `pytest` para testing
- `werkzeug.security` para hashing de contraseñas

## 4. Estructura del proyecto

```
sales_system_v2/
│
├── app.py                     # Application factory, blueprints, manejo de errores
├── config.py                  # Configuración vía variables de entorno
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── database/
│   ├── database.py            # Conexión SQLite, init_db, begin_immediate
│   ├── schema.sql             # DDL: tablas, CHECK constraints, índices
│   ├── seed.py                # Datos de prueba (usuarios, clientes, productos)
│   └── sales.db                # Se genera al iniciar la app (no versionado)
│
├── routes/
│   ├── auth.py                 # login, logout, me
│   ├── productos.py             # CRUD productos
│   ├── clientes.py              # CRUD clientes
│   ├── ventas.py                # registrar/listar/obtener ventas
│   ├── reportes.py              # reportes SQL
│   └── usuarios.py              # gestión de usuarios (ADMIN)
│
├── services/
│   ├── auth_service.py         # hashing, decoradores de auth/rol
│   ├── venta_service.py        # lógica de negocio de ventas (transacciones)
│   └── validators.py           # validaciones compartidas
│
├── tests/
│   ├── conftest.py             # fixtures (app, client, datos de prueba)
│   ├── test_auth.py
│   ├── test_productos.py
│   ├── test_clientes.py
│   ├── test_ventas.py          # incluye transacciones, rollback, concurrencia, idempotencia
│   ├── test_reportes.py
│   ├── test_usuarios.py
│   └── test_errores.py
│
└── frontend/
    ├── login.html
    ├── index.html               # nueva venta (carrito de productos)
    ├── ventas.html               # historial de ventas
    ├── admin.html                # administración (productos/clientes/usuarios/reportes)
    ├── app.js                    # helper de API compartido
    └── styles.css
```

## 5. Instalación

```bash
cd sales_system_v2
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 6. Configuración

```bash
cp .env.example .env
# Editar .env y definir una SECRET_KEY propia, por ejemplo:
python -c "import secrets; print(secrets.token_hex(32))"
```

Variables disponibles (ver `.env.example`):

| Variable                  | Descripción                                      | Default                    |
|---------------------------|---------------------------------------------------|-----------------------------|
| `SECRET_KEY`              | Firma las cookies de sesión                        | (aleatoria si no se define) |
| `DATABASE_PATH`           | Ruta al archivo SQLite                             | `database/sales.db`         |
| `SESSION_LIFETIME_MINUTES`| Minutos de duración de la sesión                   | `60`                         |
| `FLASK_ENV`               | `development` / `testing` / `production`           | `development`                |

## 7. Creación de la base de datos y datos de prueba

La base de datos y sus tablas se crean automáticamente al iniciar la
aplicación (`init_db` se ejecuta dentro de `create_app`). Para cargar
datos de prueba (usuarios, clientes y productos de ejemplo):

```bash
python -m database.seed
```

## 8. Ejecución

```bash
python app.py
```

La API y el frontend quedan disponibles en `http://localhost:5000`.
Abrir esa URL en el navegador para usar la interfaz (redirige a
`login.html` si no hay sesión iniciada mediante el propio flujo de la
app — la pantalla inicial es `index.html`, desde ahí se navega a
`login.html`).

## 9. Usuarios de prueba

Creados por `python -m database.seed`:

| Rol      | Email                | Contraseña   |
|----------|-----------------------|--------------|
| ADMIN    | admin@sistema.com      | Admin123!    |
| VENDEDOR | vendedor@sistema.com   | Vendedor123! |

Estas son credenciales de desarrollo, no secretos reales.

## 10. Endpoints principales

Todos los endpoints (salvo `/auth/login` y archivos estáticos)
requieren sesión iniciada (`@login_required`). Los marcados con
**(ADMIN)** requieren además ese rol.

### Autenticación
```
POST   /auth/login          { email, password }        -> datos del usuario
POST   /auth/logout                                     -> cierra sesión
GET    /auth/me                                          -> usuario actual
```

### Productos
```
GET    /productos                       ?categoria=&incluir_inactivos=true
GET    /productos/<id>
POST   /productos            (ADMIN)     { nombre, precio, stock, descripcion?, categoria? }
PUT    /productos/<id>       (ADMIN)
DELETE /productos/<id>       (ADMIN)     -> baja lógica (activo=0)
```

### Clientes
```
GET    /clientes                        ?incluir_inactivos=true
GET    /clientes/<id>
POST   /clientes                         { nombre, email, telefono? }
PUT    /clientes/<id>        (ADMIN)
DELETE /clientes/<id>        (ADMIN)
```

### Usuarios (ADMIN)
```
GET    /usuarios
POST   /usuarios                         { nombre, email, password, rol }
PUT    /usuarios/<id>
```

### Ventas
```
POST   /ventas                           { cliente_id, items: [{producto_id, cantidad}] }
                                          Header opcional: Idempotency-Key
GET    /ventas                           ?cliente_id=   (VENDEDOR ve solo las propias)
GET    /ventas/<id>
```

### Reportes (ADMIN)
```
GET    /reportes/ventas                  ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
GET    /reportes/ventas-diarias
GET    /reportes/productos-mas-vendidos  ?limite=10
GET    /reportes/stock-bajo              ?umbral=5
```

### Ejemplo: crear una venta

Request:
```json
POST /ventas
Content-Type: application/json
Idempotency-Key: 3f6a9d2e-...

{
  "cliente_id": 1,
  "items": [
    { "producto_id": 1, "cantidad": 1 },
    { "producto_id": 2, "cantidad": 2 }
  ]
}
```

Response (`201 Created`):
```json
{
  "id": 15,
  "cliente_id": 1,
  "usuario_id": 2,
  "total": 675.00,
  "estado": "CONFIRMADA",
  "items": [
    { "producto_id": 1, "nombre": "Laptop 14\" Core i5", "cantidad": 1, "precio_unitario": 650.0, "subtotal": 650.0 },
    { "producto_id": 2, "nombre": "Mouse inalámbrico", "cantidad": 2, "precio_unitario": 12.5, "subtotal": 25.0 }
  ]
}
```

Error de stock insuficiente (`409 Conflict`):
```json
{ "error": "Stock insuficiente para 'Mouse inalámbrico' (disponible: 1, solicitado: 2)" }
```

## 11. Autenticación y autorización — detalle técnico

- La sesión se implementa con el mecanismo nativo de Flask: una cookie
  firmada con `SECRET_KEY` que guarda `user_id` y `rol`. No se usa JWT
  porque no hay necesidad de validar la sesión fuera de este mismo
  backend.
- `@login_required` verifica que exista una sesión válida y que el
  usuario siga activo.
- `@role_required(*roles)` verifica además que el rol del usuario
  autenticado esté en la lista permitida (autorización, distinta de
  autenticación).
- Las contraseñas se almacenan con `werkzeug.security.generate_password_hash`
  (PBKDF2 con salt), nunca en texto plano.

## 12. Concurrencia y transacciones — detalle técnico

El problema clásico: `stock = 1`, dos clientes compran al mismo
tiempo. Sin protección, ambos podrían leer `stock=1`, ambos decidir
que hay stock suficiente, y terminar vendiendo 2 unidades de un
producto con solo 1 disponible.

Solución implementada (sin Redis ni PostgreSQL, solo SQLite):

1. Cada venta abre una transacción con `BEGIN IMMEDIATE`, que toma el
   lock de escritura de la base **al inicio**, no al primer `INSERT`.
2. El descuento de stock se hace con un único `UPDATE` condicional:
   `UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?`.
   La verificación y la escritura ocurren en la misma sentencia
   atómica; no hay ventana entre "leer" y "escribir" en la que otra
   transacción pueda colarse.
3. Si el `UPDATE` afecta 0 filas, significa que no había stock
   suficiente: se lanza un error y se hace `ROLLBACK` de toda la
   transacción (incluyendo cualquier otro producto ya descontado en el
   mismo pedido).
4. `PRAGMA busy_timeout` hace que una segunda transacción que llegue
   mientras la primera tiene el lock espere en vez de fallar
   inmediatamente con "database is locked".

Esto está verificado en `tests/test_ventas.py::test_concurrencia_no_vende_mas_stock_del_disponible`,
que lanza dos requests reales en hilos separados contra un producto
con `stock=1` y confirma que exactamente una tiene éxito.

## 13. Idempotencia — detalle técnico

`POST /ventas` acepta un header opcional `Idempotency-Key`. Si el
cliente reintenta la misma solicitud (por ejemplo, doble clic o un
timeout que hace reintentar al frontend) con la misma clave, el
backend devuelve la venta que ya se creó la primera vez en lugar de
crear una segunda. La clave se guarda en la tabla `idempotency_keys`
con una restricción `UNIQUE`, dentro de la misma transacción que crea
la venta.

## 14. Ejecución de tests

```bash
pytest                     # correr toda la suite
pytest -v                  # con detalle de cada test
pytest tests/test_ventas.py -v   # solo el módulo de ventas
```

Cada test usa una base de datos SQLite en un archivo temporal propio
(no `sales.db`), así que correr los tests nunca afecta a los datos de
desarrollo.

## 15. Limitaciones conocidas

- La sesión es una simple cookie de Flask; no hay refresh tokens ni
  revocación distribuida (no hace falta para un backend monolítico de
  portfolio).
- No se implementó paginación en los listados (`GET /productos`,
  `GET /ventas`, etc.); para un dataset de portfolio no es
  necesaria, pero sería el siguiente paso natural en un proyecto real.
- El frontend es intencionalmente simple (sin framework) porque el
  foco del proyecto es el backend.
- Una venta no tiene un endpoint de anulación/reembolso implementado
  (el campo `estado` soporta `ANULADA` en el esquema, pero no hay
  endpoint que lo use todavía).
- No hay rate limiting en `/auth/login` (protección básica contra
  fuerza bruta) — quedaría como mejora de seguridad futura.
