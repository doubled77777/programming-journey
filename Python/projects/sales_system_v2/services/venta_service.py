"""
Servicio de ventas: el corazón del sistema.

Responsable de:
- Validar el pedido (productos existen, cantidades válidas).
- Calcular precios y totales SIEMPRE en el backend (nunca confiar en
  lo que mande el cliente).
- Ejecutar la creación de la venta + detalle + descuento de stock como
  una única transacción atómica.
- Evitar sobreventa bajo concurrencia.
- Evitar ventas duplicadas ante reintentos (idempotencia).
"""
import json
import sqlite3
from services.validators import ValidationError, validate_cantidad
from database.database import get_db, begin_immediate


class VentaError(Exception):
    """Error de negocio al procesar una venta -> se mapea a un HTTP status."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _validar_items(items):
    if not isinstance(items, list) or len(items) == 0:
        raise ValidationError("Debe incluir al menos un producto ('items')")

    productos_vistos = set()
    items_limpios = []
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("Cada item debe ser un objeto con producto_id y cantidad")
        if "producto_id" not in item or "cantidad" not in item:
            raise ValidationError("Cada item requiere 'producto_id' y 'cantidad'")

        producto_id = item["producto_id"]
        if isinstance(producto_id, bool) or not isinstance(producto_id, int):
            raise ValidationError("'producto_id' debe ser un entero")

        cantidad = validate_cantidad(item["cantidad"])

        if producto_id in productos_vistos:
            raise ValidationError(
                f"El producto {producto_id} está repetido en el pedido; "
                "combine las cantidades en un solo item"
            )
        productos_vistos.add(producto_id)
        items_limpios.append({"producto_id": producto_id, "cantidad": cantidad})

    return items_limpios


def _buscar_idempotencia(db, clave, usuario_id):
    if not clave:
        return None
    row = db.execute(
        "SELECT * FROM idempotency_keys WHERE clave = ?", (clave,)
    ).fetchone()
    if row is None:
        return None
    if row["usuario_id"] != usuario_id:
        # Otra clave igual usada por otro usuario: no la reutilizamos.
        return None
    return {
        "status_code": row["response_status"],
        "body": json.loads(row["response_body"]),
    }


def crear_venta(cliente_id, items, usuario_id, idempotency_key=None):
    """
    Crea una venta de forma atómica y segura frente a concurrencia.

    Flujo:
      1. Validar forma de los datos (no confiar en el input).
      2. Si viene idempotency_key y ya se usó, devolver la respuesta guardada
         en vez de crear una venta nueva.
      3. Abrir una transacción con BEGIN IMMEDIATE (toma el lock de
         escritura ya, evitando la carrera de "leer stock antes de que
         nadie escriba").
      4. Verificar cliente existe y está activo.
      5. Por cada item: leer producto, validar que existe/está activo,
         y descontar stock con un UPDATE condicional
         (`WHERE stock >= cantidad`) que falla atómicamente si no alcanza.
      6. Calcular subtotales y total en el backend.
      7. Insertar venta + detalle.
      8. Commit. Si algo falla en el camino, rollback completo:
         no debe quedar ni venta a medias ni stock descontado a medias.
    """
    items = _validar_items(items)

    if isinstance(cliente_id, bool) or not isinstance(cliente_id, int):
        raise ValidationError("'cliente_id' debe ser un entero")

    db = get_db()

    cached = _buscar_idempotencia(db, idempotency_key, usuario_id)
    if cached is not None:
        return cached["body"], cached["status_code"], True  # (body, status, fue_repetida)

    begin_immediate(db)
    try:
        cliente = db.execute(
            "SELECT id, activo FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        if cliente is None:
            raise VentaError("El cliente no existe", 404)
        if not cliente["activo"]:
            raise VentaError("El cliente está inactivo", 400)

        detalles = []
        total = 0.0

        for item in items:
            producto = db.execute(
                "SELECT id, nombre, precio, stock, activo FROM productos WHERE id = ?",
                (item["producto_id"],),
            ).fetchone()
            if producto is None:
                raise VentaError(f"El producto {item['producto_id']} no existe", 404)
            if not producto["activo"]:
                raise VentaError(f"El producto '{producto['nombre']}' no está disponible", 400)

            # UPDATE condicional: esta es la clave para evitar sobreventa
            # bajo concurrencia. La condición stock >= cantidad se evalúa
            # y aplica de forma atómica en la misma sentencia SQL; no hay
            # ventana entre "leer stock" y "escribir stock" en la que otra
            # transacción pueda colarse (ya tenemos además el lock de
            # escritura por BEGIN IMMEDIATE).
            cursor = db.execute(
                "UPDATE productos SET stock = stock - ? "
                "WHERE id = ? AND stock >= ?",
                (item["cantidad"], item["producto_id"], item["cantidad"]),
            )
            if cursor.rowcount == 0:
                raise VentaError(
                    f"Stock insuficiente para '{producto['nombre']}' "
                    f"(disponible: {producto['stock']}, solicitado: {item['cantidad']})",
                    409,
                )

            precio_unitario = producto["precio"]
            subtotal = round(precio_unitario * item["cantidad"], 2)
            total += subtotal
            detalles.append({
                "producto_id": producto["id"],
                "nombre": producto["nombre"],
                "cantidad": item["cantidad"],
                "precio_unitario": precio_unitario,
                "subtotal": subtotal,
            })

        total = round(total, 2)

        cursor = db.execute(
            "INSERT INTO ventas (cliente_id, usuario_id, total, estado) "
            "VALUES (?, ?, ?, 'CONFIRMADA')",
            (cliente_id, usuario_id, total),
        )
        venta_id = cursor.lastrowid

        for d in detalles:
            db.execute(
                "INSERT INTO detalle_venta "
                "(venta_id, producto_id, cantidad, precio_unitario, subtotal) "
                "VALUES (?, ?, ?, ?, ?)",
                (venta_id, d["producto_id"], d["cantidad"], d["precio_unitario"], d["subtotal"]),
            )

        body = {
            "id": venta_id,
            "cliente_id": cliente_id,
            "usuario_id": usuario_id,
            "total": total,
            "estado": "CONFIRMADA",
            "items": detalles,
        }
        status_code = 201

        if idempotency_key:
            try:
                db.execute(
                    "INSERT INTO idempotency_keys "
                    "(clave, usuario_id, venta_id, response_body, response_status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (idempotency_key, usuario_id, venta_id, json.dumps(body), status_code),
                )
            except sqlite3.IntegrityError:
                # Carrera rarísima: dos requests con la misma clave llegaron
                # a la vez y ambas pasaron el chequeo inicial. Como el UPDATE
                # de stock y el INSERT de venta ya se hicieron en ESTA
                # transacción, y la clave ya existe, abortamos esta venta
                # (rollback) y devolvemos la que quedó registrada primero.
                db.execute("ROLLBACK")
                cached = _buscar_idempotencia(db, idempotency_key, usuario_id)
                if cached is not None:
                    return cached["body"], cached["status_code"], True
                raise

        db.execute("COMMIT")
        return body, status_code, False

    except Exception:
        db.execute("ROLLBACK")
        raise


def listar_ventas(cliente_id=None, usuario_id=None, rol=None):
    """
    VENDEDOR solo puede ver sus propias ventas; ADMIN ve todas
    (o filtradas por cliente si se pide).
    """
    db = get_db()
    query = (
        "SELECT v.id, v.cliente_id, c.nombre AS cliente_nombre, v.usuario_id, "
        "v.fecha, v.total, v.estado "
        "FROM ventas v JOIN clientes c ON c.id = v.cliente_id WHERE 1=1"
    )
    params = []

    if rol != "ADMIN":
        query += " AND v.usuario_id = ?"
        params.append(usuario_id)

    if cliente_id is not None:
        query += " AND v.cliente_id = ?"
        params.append(cliente_id)

    query += " ORDER BY v.fecha DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def obtener_venta(venta_id, usuario_id=None, rol=None):
    db = get_db()
    venta = db.execute(
        "SELECT v.*, c.nombre AS cliente_nombre FROM ventas v "
        "JOIN clientes c ON c.id = v.cliente_id WHERE v.id = ?",
        (venta_id,),
    ).fetchone()
    if venta is None:
        return None
    if rol != "ADMIN" and venta["usuario_id"] != usuario_id:
        return "forbidden"

    items = db.execute(
        "SELECT dv.producto_id, p.nombre, dv.cantidad, dv.precio_unitario, dv.subtotal "
        "FROM detalle_venta dv JOIN productos p ON p.id = dv.producto_id "
        "WHERE dv.venta_id = ?",
        (venta_id,),
    ).fetchall()

    result = dict(venta)
    result["items"] = [dict(i) for i in items]
    return result
