from flask import Blueprint, request, jsonify

from database.database import get_db
from services.auth_service import role_required

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


@reportes_bp.get("/ventas")
@role_required("ADMIN")
def reporte_ventas():
    """Listado de ventas con filtro opcional por rango de fechas."""
    desde = request.args.get("desde")  # 'YYYY-MM-DD'
    hasta = request.args.get("hasta")

    db = get_db()
    query = (
        "SELECT v.id, v.fecha, c.nombre AS cliente, u.nombre AS vendedor, "
        "v.total, v.estado "
        "FROM ventas v "
        "JOIN clientes c ON c.id = v.cliente_id "
        "JOIN usuarios u ON u.id = v.usuario_id "
        "WHERE 1=1"
    )
    params = []
    if desde:
        query += " AND date(v.fecha) >= date(?)"
        params.append(desde)
    if hasta:
        query += " AND date(v.fecha) <= date(?)"
        params.append(hasta)
    query += " ORDER BY v.fecha DESC"

    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows]), 200


@reportes_bp.get("/ventas-diarias")
@role_required("ADMIN")
def reporte_ventas_diarias():
    """Totales de ventas agrupados por día."""
    db = get_db()
    rows = db.execute(
        "SELECT date(fecha) AS dia, COUNT(*) AS cantidad_ventas, "
        "SUM(total) AS total_vendido "
        "FROM ventas "
        "WHERE estado = 'CONFIRMADA' "
        "GROUP BY date(fecha) "
        "ORDER BY dia DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows]), 200


@reportes_bp.get("/productos-mas-vendidos")
@role_required("ADMIN")
def reporte_productos_mas_vendidos():
    """Ranking de productos por unidades vendidas."""
    limite = request.args.get("limite", default=10, type=int)
    db = get_db()
    rows = db.execute(
        "SELECT p.id, p.nombre, SUM(dv.cantidad) AS unidades_vendidas, "
        "SUM(dv.subtotal) AS total_generado "
        "FROM detalle_venta dv "
        "JOIN productos p ON p.id = dv.producto_id "
        "JOIN ventas v ON v.id = dv.venta_id "
        "WHERE v.estado = 'CONFIRMADA' "
        "GROUP BY p.id "
        "ORDER BY unidades_vendidas DESC "
        "LIMIT ?",
        (limite,),
    ).fetchall()
    return jsonify([dict(r) for r in rows]), 200


@reportes_bp.get("/stock-bajo")
@role_required("ADMIN")
def reporte_stock_bajo():
    """Productos activos con stock igual o por debajo de un umbral."""
    umbral = request.args.get("umbral", default=5, type=int)
    db = get_db()
    rows = db.execute(
        "SELECT id, nombre, stock, categoria "
        "FROM productos "
        "WHERE activo = 1 AND stock <= ? "
        "ORDER BY stock ASC",
        (umbral,),
    ).fetchall()
    return jsonify([dict(r) for r in rows]), 200
