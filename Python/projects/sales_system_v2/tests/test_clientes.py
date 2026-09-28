from tests.conftest import login


def test_crear_cliente_ok(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/clientes", json={"nombre": "Nuevo Cliente", "email": "nuevo@test.com"})
    assert resp.status_code == 201
    assert resp.get_json()["email"] == "nuevo@test.com"


def test_crear_cliente_email_invalido(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/clientes", json={"nombre": "X", "email": "no-es-un-email"})
    assert resp.status_code == 400


def test_crear_cliente_email_duplicado(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/clientes", json={"nombre": "Dup", "email": "cliente@test.com"})
    assert resp.status_code == 409


def test_crear_cliente_nombre_vacio(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/clientes", json={"nombre": "", "email": "algo@test.com"})
    assert resp.status_code == 400


def test_listar_clientes_ok(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.get("/clientes")
    assert resp.status_code == 200
    assert len(resp.get_json()) >= 1


def test_actualizar_cliente_requiere_admin(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.put(f"/clientes/{seed_basico['cliente_id']}", json={"nombre": "Cambiado"})
    assert resp.status_code == 403
