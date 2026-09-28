from tests.conftest import login


def test_crear_usuario_admin_ok(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/usuarios", json={
        "nombre": "Nuevo", "email": "nuevo@test.com", "password": "Clave123!", "rol": "VENDEDOR",
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert "password_hash" not in body
    assert "password" not in body


def test_crear_usuario_password_corta_rechazada(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/usuarios", json={
        "nombre": "X", "email": "x@test.com", "password": "123", "rol": "VENDEDOR",
    })
    assert resp.status_code == 400


def test_crear_usuario_rol_invalido_rechazado(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/usuarios", json={
        "nombre": "X", "email": "x@test.com", "password": "Clave123!", "rol": "SUPERADMIN",
    })
    assert resp.status_code == 400


def test_crear_usuario_email_duplicado(client, seed_basico):
    login(client, **seed_basico["admin"])
    resp = client.post("/usuarios", json={
        "nombre": "X", "email": "admin@test.com", "password": "Clave123!", "rol": "VENDEDOR",
    })
    assert resp.status_code == 409


def test_crear_usuario_requiere_admin(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/usuarios", json={
        "nombre": "X", "email": "x@test.com", "password": "Clave123!", "rol": "VENDEDOR",
    })
    assert resp.status_code == 403


def test_listar_usuarios_requiere_admin(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.get("/usuarios")
    assert resp.status_code == 403

    client.post("/auth/logout")
    login(client, **seed_basico["admin"])
    resp = client.get("/usuarios")
    assert resp.status_code == 200
