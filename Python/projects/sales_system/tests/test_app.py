"""
Suite de pruebas del backend.

No se realiza ningún cobro real: `cobrar_con_mercadopago` se reemplaza por un
mock en cada test que lo necesita, siguiendo exactamente el mismo patrón que
se usaría para probar cualquier integración externa sin depender de que esa
API de verdad esté disponible (o cobre dinero real) cada vez que se corren
los tests.
"""
import sqlite3
import threading

import app as app_module
import repository
from config import Config
from services.mercadopago_service import PaymentError


def _post_order(client, **overrides):
    payload = {
        "producto_id": 1,
        "cantidad": 1,
        "token": "fake-token",
        "client_request_id": "req-1",
        "payment_method_id": "visa",
        "payer": {"email": "comprador@test.com"},
    }
    payload.update(overrides)
    return client.post("/process_order", json=payload)


def _mock_pago(aprobado=True, order_id="ORD123"):
    def _fake(_datos_formulario, _total, idempotency_key=None):
        return {
            "aprobado": aprobado,
            "order_id": order_id,
            "status": "processed" if aprobado else "failed",
            "status_detail": "accredited" if aprobado else "rejected_by_issuer",
        }
    return _fake


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------

def test_listar_productos(client):
    response = client.get("/productos")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Producto de prueba"


def test_obtener_producto_inexistente(client):
    response = client.get("/productos/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Venta correcta
# ---------------------------------------------------------------------------

def test_venta_correcta_pago_aprobado(client, monkeypatch):
    monkeypatch.setattr(app_module, "cobrar_con_mercadopago", _mock_pago(aprobado=True))

    response = _post_order(client, cantidad=2, client_request_id="req-correcto")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["total"] == 200.0
    assert data["order_id"] == "ORD123"

    producto = client.get("/productos/1").get_json()
    assert producto["stock"] == 3  # 5 - 2


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------

def test_producto_inexistente(client, monkeypatch):
    monkeypatch.setattr(app_module, "cobrar_con_mercadopago", _mock_pago(aprobado=True))
    response = _post_order(client, producto_id=999, client_request_id="req-sin-producto")
    assert response.status_code == 404


def test_cantidad_cero_es_invalida(client):
    response = _post_order(client, cantidad=0, client_request_id="req-cero")
    assert response.status_code == 400


def test_cantidad_negativa_es_invalida(client):
    response = _post_order(client, cantidad=-1, client_request_id="req-negativo")
    assert response.status_code == 400


def test_cantidad_con_tipo_incorrecto_es_invalida(client):
    response = _post_order(client, cantidad="dos", client_request_id="req-tipo-malo")
    assert response.status_code == 400


def test_falta_client_request_id(client):
    response = _post_order(client, client_request_id=None)
    assert response.status_code == 400


def test_falta_token(client):
    response = _post_order(client, token=None, client_request_id="req-sin-token")
    assert response.status_code == 400


def test_cuerpo_no_json_es_rechazado(client):
    response = client.post("/process_order", data="esto no es json", content_type="text/plain")
    assert response.status_code == 400


def test_stock_insuficiente(client, monkeypatch):
    monkeypatch.setattr(app_module, "cobrar_con_mercadopago", _mock_pago(aprobado=True))
    response = _post_order(client, cantidad=100, client_request_id="req-sin-stock")
    assert response.status_code == 400
    assert "stock" in response.get_json()["message"].lower()


# ---------------------------------------------------------------------------
# Pago rechazado: no debe registrar venta ni descontar stock
# ---------------------------------------------------------------------------

def test_pago_rechazado_no_registra_venta_ni_descuenta_stock(client, monkeypatch):
    monkeypatch.setattr(app_module, "cobrar_con_mercadopago", _mock_pago(aprobado=False))

    response = _post_order(client, cantidad=1, client_request_id="req-rechazo")
    assert response.status_code == 402

    producto = client.get("/productos/1").get_json()
    assert producto["stock"] == 5  # sin cambios

    assert repository.listar_ventas() == []


# ---------------------------------------------------------------------------
# Errores de integración con Mercado Pago (red, timeout)
# ---------------------------------------------------------------------------

def test_error_de_red_con_mercado_pago_no_registra_venta(client, monkeypatch):
    def _fake_error(*_args, **_kwargs):
        raise PaymentError("timeout")

    monkeypatch.setattr(app_module, "cobrar_con_mercadopago", _fake_error)

    response = _post_order(client, client_request_id="req-timeout")
    assert response.status_code == 502

    producto = client.get("/productos/1").get_json()
    assert producto["stock"] == 5
    assert repository.listar_ventas() == []


# ---------------------------------------------------------------------------
# Idempotencia / solicitudes duplicadas
# ---------------------------------------------------------------------------

def test_solicitud_duplicada_no_duplica_venta_ni_cobra_dos_veces(client, monkeypatch):
    llamadas = {"contador": 0}

    def fake_pago(_datos_formulario, _total, idempotency_key=None):
        llamadas["contador"] += 1
        return {"aprobado": True, "order_id": "ORD-DUP", "status": "processed", "status_detail": "accredited"}

    monkeypatch.setattr(app_module, "cobrar_con_mercadopago", fake_pago)

    r1 = _post_order(client, cantidad=1, client_request_id="req-dup")
    r2 = _post_order(client, cantidad=1, client_request_id="req-dup")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert llamadas["contador"] == 1  # Mercado Pago solo se llamó una vez

    producto = client.get("/productos/1").get_json()
    assert producto["stock"] == 4  # el stock solo se descontó una vez

    assert len(repository.listar_ventas()) == 1


# ---------------------------------------------------------------------------
# Autenticación / autorización de rutas administrativas
# ---------------------------------------------------------------------------

def test_ruta_admin_sin_api_key_es_rechazada(client):
    response = client.get("/ventas")
    assert response.status_code == 401


def test_ruta_admin_con_api_key_incorrecta_es_rechazada(client, monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_API_KEY", "clave-correcta")
    response = client.get("/ventas", headers={"X-API-Key": "clave-incorrecta"})
    assert response.status_code == 401


def test_ruta_admin_con_api_key_correcta_funciona(client, monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_API_KEY", "clave-correcta")
    response = client.get("/ventas", headers={"X-API-Key": "clave-correcta"})
    assert response.status_code == 200


def test_crud_productos_como_admin(client, monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_API_KEY", "clave-correcta")
    headers = {"X-API-Key": "clave-correcta"}

    creado = client.post("/productos", json={"nombre": "Monitor", "precio": 500, "stock": 3}, headers=headers)
    assert creado.status_code == 201
    nuevo_id = creado.get_json()["id"]

    actualizado = client.put(f"/productos/{nuevo_id}", json={"stock": 10}, headers=headers)
    assert actualizado.status_code == 200
    assert client.get(f"/productos/{nuevo_id}").get_json()["stock"] == 10

    eliminado = client.delete(f"/productos/{nuevo_id}", headers=headers)
    assert eliminado.status_code == 200
    assert client.get(f"/productos/{nuevo_id}").status_code == 404


def test_crear_producto_con_precio_negativo_es_invalido(client, monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_API_KEY", "clave-correcta")
    response = client.post(
        "/productos",
        json={"nombre": "Malo", "precio": -10, "stock": 1},
        headers={"X-API-Key": "clave-correcta"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Concurrencia: stock = 1, varios compradores simultáneos
# ---------------------------------------------------------------------------

def test_concurrencia_nunca_vende_mas_stock_del_disponible(db_path):
    """
    Reproduce el escenario "stock = 1, dos (o más) clientes compran al mismo
    tiempo": lanza 5 hilos intentando comprar la única unidad disponible a
    la vez, y comprueba que solo UNO tiene éxito y el stock final es 0
    (nunca negativo, nunca vendido más de una vez).
    """
    conexion = sqlite3.connect(db_path)
    conexion.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL CHECK (precio >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
        )
    """)
    conexion.execute("""
        CREATE TABLE ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL CHECK (cantidad > 0),
            total REAL NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now')),
            order_id TEXT,
            client_request_id TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    """)
    conexion.execute("INSERT INTO productos (nombre, precio, stock) VALUES ('Único', 100.0, 1)")
    conexion.commit()
    conexion.close()

    Config.DB_PATH = db_path
    resultados = []

    def intentar_compra():
        try:
            repository.registrar_venta_y_descontar_stock(
                producto_id=1, cantidad=1, total=100.0,
                order_id=f"ORD-{threading.get_ident()}",
                client_request_id=f"req-{threading.get_ident()}",
            )
            resultados.append("ok")
        except repository.StockInsuficienteError:
            resultados.append("sin_stock")

    hilos = [threading.Thread(target=intentar_compra) for _ in range(5)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert resultados.count("ok") == 1
    assert resultados.count("sin_stock") == 4

    conexion = sqlite3.connect(db_path)
    stock_final = conexion.execute("SELECT stock FROM productos WHERE id = 1").fetchone()[0]
    total_ventas = conexion.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    conexion.close()

    assert stock_final == 0
    assert total_ventas == 1
