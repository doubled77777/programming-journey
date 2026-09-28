from tests.conftest import login


def test_json_invalido_devuelve_400(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post(
        "/productos",
        data="esto no es json{{{",
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_tipo_incorrecto_en_precio(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/productos", json={"nombre": "X", "precio": "gratis", "stock": 1})
    assert resp.status_code == 400


def test_tipo_incorrecto_en_cantidad_de_venta(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": "dos"}],
    })
    assert resp.status_code == 400


def test_ruta_inexistente_devuelve_404_json(client, seed_basico):
    resp = client.get("/esto-no-existe")
    assert resp.status_code == 404
    assert resp.get_json() is not None


def test_metodo_no_permitido(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.patch("/productos")
    assert resp.status_code == 405
