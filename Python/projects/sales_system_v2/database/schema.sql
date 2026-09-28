-- Esquema del sistema de ventas.
-- Diseñado para SQLite. Usa CHECK constraints para reforzar reglas de
-- negocio (precios/stock no negativos) directamente en la base de datos,
-- como última línea de defensa además de la validación en el backend.

PRAGMA foreign_keys = ON;

-- =========================================================
-- USUARIOS (login al sistema: ADMIN / VENDEDOR)
-- =========================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK (rol IN ('ADMIN', 'VENDEDOR')),
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    fecha_creacion  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================================================
-- CLIENTES
-- =========================================================
CREATE TABLE IF NOT EXISTS clientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    email           TEXT NOT NULL UNIQUE,
    telefono        TEXT,
    fecha_creacion  TEXT NOT NULL DEFAULT (datetime('now')),
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- =========================================================
-- PRODUCTOS
-- =========================================================
CREATE TABLE IF NOT EXISTS productos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    descripcion     TEXT,
    precio          REAL NOT NULL CHECK (precio >= 0),
    stock           INTEGER NOT NULL CHECK (stock >= 0),
    categoria       TEXT,
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    fecha_creacion  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);
CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo);

-- =========================================================
-- VENTAS
-- =========================================================
CREATE TABLE IF NOT EXISTS ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL,
    usuario_id      INTEGER NOT NULL,
    fecha           TEXT NOT NULL DEFAULT (datetime('now')),
    total           REAL NOT NULL CHECK (total >= 0),
    estado          TEXT NOT NULL DEFAULT 'CONFIRMADA'
                        CHECK (estado IN ('CONFIRMADA', 'ANULADA')),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);

-- =========================================================
-- DETALLE DE VENTA
-- =========================================================
CREATE TABLE IF NOT EXISTS detalle_venta (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id        INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0),
    subtotal        REAL NOT NULL CHECK (subtotal >= 0),
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE INDEX IF NOT EXISTS idx_detalle_venta_venta ON detalle_venta(venta_id);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_producto ON detalle_venta(producto_id);

-- =========================================================
-- IDEMPOTENCIA: registra claves de idempotencia usadas en POST /ventas
-- para evitar crear ventas duplicadas ante reintentos/doble clic.
-- =========================================================
CREATE TABLE IF NOT EXISTS idempotency_keys (
    clave           TEXT PRIMARY KEY,
    usuario_id      INTEGER NOT NULL,
    venta_id        INTEGER,
    response_body   TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    fecha_creacion  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);
