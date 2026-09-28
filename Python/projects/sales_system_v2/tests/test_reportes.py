from tests.conftest import login


def _crear_venta(client, seed_basico, producto_id, cantidad):
    return client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": producto_id, "cantidad": cantidad}],
    })


def test_reportes_requieren_admin(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    for path in [
        "/reportes/ventas", "/reportes/ventas-diarias",
        "/reportes/productos-mas-vendidos", "/reportes/stock-bajo",
    ]:
        resp = client.get(path)
        assert resp.status_code == 403, f"{path} debería requerir rol ADMIN"


def test_reporte_ventas(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    _crear_venta(client, seed_basico, seed_basico["producto_a_id"], 1)
    client.post("/auth/logout")

    login(client, **seed_basico["admin"])
    resp = client.get("/reportes/ventas")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["cliente"] == "Cliente Test"
    assert data[0]["vendedor"] == "Vendedor"


def test_reporte_ventas_diarias(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    _crear_venta(client, seed_basico, seed_basico["producto_a_id"], 2)
    client.post("/auth/logout")

    login(client, **seed_basico["admin"])
    resp = client.get("/reportes/ventas-diarias")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["cantidad_ventas"] == 1
    assert data[0]["total_vendido"] == 20.0


def test_reporte_productos_mas_vendidos(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    _crear_venta(client, seed_basico, seed_basico["producto_a_id"], 3)
    client.post("/auth/logout")

    login(client, **seed_basico["admin"])
    resp = client.get("/reportes/productos-mas-vendidos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]["nombre"] == "Producto A"
    assert data[0]["unidades_vendidas"] == 3


def test_reporte_stock_bajo(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.get("/reportes/stock-bajo?umbral=1")
    assert resp.status_code == 200
    nombres = [p["nombre"] for p in resp.get_json()]
    assert "Producto Único" in nombres
    assert "Producto A" not in nombres
