from tests.conftest import login


def test_crear_producto_admin_ok(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/productos", json={
        "nombre": "Nuevo producto", "precio": 9.99, "stock": 10, "categoria": "X",
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["nombre"] == "Nuevo producto"
    assert body["activo"] is True


def test_crear_producto_precio_negativo_rechazado(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/productos", json={"nombre": "Malo", "precio": -5, "stock": 1})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_crear_producto_stock_negativo_rechazado(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/productos", json={"nombre": "Malo", "precio": 5, "stock": -1})
    assert resp.status_code == 400


def test_crear_producto_nombre_vacio_rechazado(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/productos", json={"nombre": "   ", "precio": 5, "stock": 1})
    assert resp.status_code == 400


def test_crear_producto_vendedor_no_autorizado(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/productos", json={"nombre": "X", "precio": 5, "stock": 1})
    assert resp.status_code == 403


def test_listar_productos_requiere_login(client, seed_basico):
    resp = client.get("/productos")
    assert resp.status_code == 401


def test_listar_productos_ok(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.get("/productos")
    assert resp.status_code == 200
    nombres = [p["nombre"] for p in resp.get_json()]
    assert "Producto A" in nombres


def test_obtener_producto_inexistente(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.get("/productos/99999")
    assert resp.status_code == 404


def test_eliminar_producto_es_baja_logica(client, seed_basico):
    login(client, **seed_basico["admin"])
    pid = seed_basico["producto_a_id"]
    resp = client.delete(f"/productos/{pid}")
    assert resp.status_code == 200

    resp = client.get(f"/productos/{pid}")
    assert resp.status_code == 200
    assert resp.get_json()["activo"] is False

    resp = client.get("/productos")
    nombres = [p["nombre"] for p in resp.get_json()]
    assert "Producto A" not in nombres
