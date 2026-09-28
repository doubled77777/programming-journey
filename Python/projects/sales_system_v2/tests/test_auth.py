from tests.conftest import login


def test_login_ok(client, seed_basico):
    resp = login(client, **seed_basico["admin"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rol"] == "ADMIN"
    assert "password" not in body
    assert "password_hash" not in body


def test_login_password_incorrecta(client, seed_basico):
    resp = login(client, seed_basico["admin"]["email"], "password-incorrecta")
    assert resp.status_code == 401


def test_login_usuario_inexistente(client, seed_basico):
    resp = login(client, "no-existe@test.com", "cualquiera")
    assert resp.status_code == 401


def test_login_faltan_campos(client, seed_basico):
    resp = client.post("/auth/login", json={"email": "admin@test.com"})
    assert resp.status_code == 400


def test_endpoint_protegido_sin_sesion(client, seed_basico):
    resp = client.get("/productos")
    assert resp.status_code == 401


def test_me_despues_de_login(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.get_json()["rol"] == "ADMIN"


def test_logout_invalida_sesion(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/auth/logout")
    assert resp.status_code == 200

    resp = client.get("/productos")
    assert resp.status_code == 401


def test_autorizacion_por_rol_vendedor_no_puede_crear_producto(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/productos", json={"nombre": "X", "precio": 1, "stock": 1})
    assert resp.status_code == 403


def test_autorizacion_por_rol_admin_si_puede(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/productos", json={"nombre": "X", "precio": 1, "stock": 1})
    assert resp.status_code == 201
