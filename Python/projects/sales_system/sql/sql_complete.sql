-- ============================================================
-- SISTEMA DE VENTAS - PROBLEMAS SQL RESUELTOS
-- ============================================================

-- TABLA
CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT,
    precio REAL,
    stock INTEGER
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    ciudad TEXT
);

CREATE TABLE ventas (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER,
    producto_id INTEGER,
    cantidad INTEGER,
    fecha TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);


-- ============================================================
-- DATOS
-- ============================================================

INSERT INTO productos VALUES
(1, 'Laptop', 'Computacion', 2500, 10),
(2, 'Mouse', 'Accesorios', 80, 30),
(3, 'Teclado', 'Accesorios', 150, 20),
(4, 'Monitor', 'Computacion', 900, 15),
(5, 'Audifonos', 'Audio', 200, 25);

INSERT INTO clientes VALUES
(1, 'Diego', 'Lima'),
(2, 'Carlos', 'Arequipa'),
(3, 'Ana', 'Cusco'),
(4, 'Luis', 'Lima');

INSERT INTO ventas VALUES
(1, 1, 1, 1, '2026-08-01'),
(2, 2, 3, 2, '2026-08-02'),
(3, 1, 2, 3, '2026-08-05'),
(4, 3, 4, 1, '2026-08-08');


-- ============================================================
-- PROBLEMA 1
-- Mostrar todos los productos que cuestan más de S/100.
-- ============================================================

SELECT nombre, precio
FROM productos
WHERE precio > 100;


-- ============================================================
-- PROBLEMA 2
-- Mostrar los productos de Accesorios ordenados
-- del más caro al más barato.
-- ============================================================

SELECT nombre, precio
FROM productos
WHERE categoria = 'Accesorios'
ORDER BY precio DESC;


-- ============================================================
-- PROBLEMA 3
-- ¿Cuántos productos tenemos?
-- ¿Cuál es el precio promedio?
-- ¿Cuál es el producto más caro y más barato?
-- ============================================================

SELECT
    COUNT(*) AS cantidad_productos,
    AVG(precio) AS precio_promedio,
    MAX(precio) AS precio_maximo,
    MIN(precio) AS precio_minimo
FROM productos;


-- ============================================================
-- PROBLEMA 4
-- ¿Cuántos productos existen en cada categoría?
-- ============================================================

SELECT
    categoria,
    COUNT(*) AS cantidad
FROM productos
GROUP BY categoria;


-- ============================================================
-- PROBLEMA 5
-- Mostrar solamente las categorías que tengan
-- más de un producto.
-- ============================================================

SELECT
    categoria,
    COUNT(*) AS cantidad
FROM productos
GROUP BY categoria
HAVING COUNT(*) > 1;


-- ============================================================
-- PROBLEMA 6
-- Mostrar cada venta junto con el nombre del cliente
-- y el producto comprado.
-- ============================================================

SELECT
    ventas.id AS venta,
    clientes.nombre AS cliente,
    productos.nombre AS producto,
    ventas.cantidad,
    ventas.fecha
FROM ventas
INNER JOIN clientes
    ON ventas.cliente_id = clientes.id
INNER JOIN productos
    ON ventas.producto_id = productos.id;


-- ============================================================
-- PROBLEMA 7
-- ¿Cuánto dinero representa cada venta?
-- ============================================================

SELECT
    ventas.id AS venta,
    productos.nombre AS producto,
    ventas.cantidad,
    productos.precio,
    ventas.cantidad * productos.precio AS total
FROM ventas
INNER JOIN productos
    ON ventas.producto_id = productos.id;


-- ============================================================
-- PROBLEMA 8
-- ¿Cuánto dinero ha gastado cada cliente?
-- ============================================================

SELECT
    clientes.nombre AS cliente,
    SUM(ventas.cantidad * productos.precio) AS total_gastado
FROM clientes
INNER JOIN ventas
    ON clientes.id = ventas.cliente_id
INNER JOIN productos
    ON ventas.producto_id = productos.id
GROUP BY clientes.id, clientes.nombre;


-- ============================================================
-- PROBLEMA 9
-- Mostrar solamente los clientes que gastaron más de S/500.
-- ============================================================

SELECT
    clientes.nombre AS cliente,
    SUM(ventas.cantidad * productos.precio) AS total_gastado
FROM clientes
INNER JOIN ventas
    ON clientes.id = ventas.cliente_id
INNER JOIN productos
    ON ventas.producto_id = productos.id
GROUP BY clientes.id, clientes.nombre
HAVING total_gastado > 500;


-- ============================================================
-- PROBLEMA 10
-- Clasificar los productos:
-- >= 2000  -> Caro
-- >= 500   -> Medio
-- < 500    -> Economico
-- ============================================================

SELECT
    nombre,
    precio,
    CASE
        WHEN precio >= 2000 THEN 'Caro'
        WHEN precio >= 500 THEN 'Medio'
        ELSE 'Economico'
    END AS clasificacion
FROM productos;


-- ============================================================
-- PROBLEMA 11
-- Mostrar los productos cuyo precio sea mayor
-- al precio promedio.
-- ============================================================

SELECT
    nombre,
    precio
FROM productos
WHERE precio > (
    SELECT AVG(precio)
    FROM productos
);


-- ============================================================
-- PROBLEMA 12
-- Mostrar el producto más caro.
-- ============================================================

SELECT
    nombre,
    precio
FROM productos
WHERE precio = (
    SELECT MAX(precio)
    FROM productos
);


-- ============================================================
-- PROBLEMA 13
-- Mostrar todos los clientes aunque no hayan comprado.
-- Si no tienen compras, mostrar 0.
-- ============================================================

SELECT
    clientes.nombre,

    COALESCE(
        SUM(ventas.cantidad * productos.precio),
        0
    ) AS total_gastado

FROM clientes

LEFT JOIN ventas
    ON clientes.id = ventas.cliente_id

LEFT JOIN productos
    ON ventas.producto_id = productos.id

GROUP BY clientes.id, clientes.nombre;


-- ============================================================
-- PROBLEMA 14
-- Mostrar los productos cuyo stock sea menor a 20
-- Y clasificarlos.
-- ============================================================

SELECT
    nombre,
    stock,

    CASE
        WHEN stock = 0 THEN 'Sin stock'
        WHEN stock < 10 THEN 'Stock bajo'
        ELSE 'Stock suficiente'
    END AS estado

FROM productos
WHERE stock < 20;


-- ============================================================
-- PROBLEMA 15
-- ¿Cuál es el producto que más unidades se ha vendido?
-- ============================================================

SELECT
    productos.nombre,
    SUM(ventas.cantidad) AS unidades_vendidas
FROM productos
INNER JOIN ventas
    ON productos.id = ventas.producto_id
GROUP BY productos.id, productos.nombre
ORDER BY unidades_vendidas DESC
LIMIT 1;


-- ============================================================
-- PROBLEMA 16
-- Mostrar los 3 productos más caros.
-- ============================================================

SELECT
    nombre,
    precio
FROM productos
ORDER BY precio DESC
LIMIT 3;


-- ============================================================
-- PROBLEMA 17
-- Aumentar en S/10 el precio de todos los accesorios.
-- ============================================================

UPDATE productos
SET precio = precio + 10
WHERE categoria = 'Accesorios';


-- ============================================================
-- PROBLEMA 18
-- Mostrar el valor total del inventario.
-- ============================================================

SELECT
    SUM(precio * stock) AS valor_inventario
FROM productos;


-- ============================================================
-- PROBLEMA 19
-- Crear una consulta temporal con WITH para obtener
-- el total gastado por cada cliente.
-- ============================================================

WITH resumen_clientes AS (

    SELECT
        clientes.nombre AS cliente,
        SUM(ventas.cantidad * productos.precio) AS total

    FROM clientes

    INNER JOIN ventas
        ON clientes.id = ventas.cliente_id

    INNER JOIN productos
        ON ventas.producto_id = productos.id

    GROUP BY clientes.id, clientes.nombre
)

SELECT *
FROM resumen_clientes
WHERE total > 500
ORDER BY total DESC;


-- ============================================================
-- PROBLEMA 20 - CONSULTA FINAL
--
-- Mostrar:
-- cliente
-- cantidad de compras
-- dinero gastado
-- categoría del cliente
-- ordenado del que más gastó al que menos gastó.
-- ============================================================

SELECT
    clientes.nombre AS cliente,

    COUNT(ventas.id) AS compras,

    SUM(
        ventas.cantidad * productos.precio
    ) AS total_gastado,

    CASE
        WHEN SUM(
            ventas.cantidad * productos.precio
        ) >= 2000
        THEN 'VIP'

        WHEN SUM(
            ventas.cantidad * productos.precio
        ) >= 500
        THEN 'Frecuente'

        ELSE 'Ocasional'
    END AS tipo_cliente

FROM clientes

LEFT JOIN ventas
    ON clientes.id = ventas.cliente_id

LEFT JOIN productos
    ON ventas.producto_id = productos.id

GROUP BY clientes.id, clientes.nombre

ORDER BY total_gastado DESC;