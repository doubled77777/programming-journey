import threading

from tests.conftest import login


def test_crear_venta_ok(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 2}],
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["total"] == 20.0  # 2 x 10.0
    assert body["estado"] == "CONFIRMADA"
    assert len(body["items"]) == 1


def test_venta_descuenta_stock(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 2}],
    })
    resp = client.get(f"/productos/{seed_basico['producto_a_id']}")
    assert resp.get_json()["stock"] == 3  # 5 - 2


def test_venta_stock_insuficiente_rechazada(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 999}],
    })
    assert resp.status_code == 409
    assert "Stock insuficiente" in resp.get_json()["error"]


def test_venta_no_deja_stock_negativo(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_unico_id"], "cantidad": 1}],
    })
    # El stock ya es 0; un segundo intento debe fallar y NO dejarlo negativo.
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_unico_id"], "cantidad": 1}],
    })
    assert resp.status_code == 409

    resp = client.get(f"/productos/{seed_basico['producto_unico_id']}")
    assert resp.get_json()["stock"] == 0


def test_venta_producto_inexistente(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": 99999, "cantidad": 1}],
    })
    assert resp.status_code == 404


def test_venta_cliente_inexistente(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": 99999,
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 1}],
    })
    assert resp.status_code == 404


def test_venta_rollback_no_descuenta_stock_de_items_previos(client, seed_basico):
    """
    Si un pedido tiene dos items y el segundo falla (sin stock), el
    descuento de stock del primer item debe revertirse: no puede quedar
    una venta a medio confirmar ni stock descontado de un pedido que
    nunca se concretó.
    """
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [
            {"producto_id": seed_basico["producto_a_id"], "cantidad": 1},   # ok, hay 5
            {"producto_id": seed_basico["producto_unico_id"], "cantidad": 5},  # falla, solo hay 1
        ],
    })
    assert resp.status_code == 409

    resp = client.get(f"/productos/{seed_basico['producto_a_id']}")
    assert resp.get_json()["stock"] == 5, "El stock del primer item no debió descontarse (rollback)"

    resp = client.get("/ventas")
    assert resp.get_json() == [], "No debe haber quedado ninguna venta registrada"


def test_venta_cantidad_invalida(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 0}],
    })
    assert resp.status_code == 400

    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": -3}],
    })
    assert resp.status_code == 400


def test_venta_sin_items_rechazada(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={"cliente_id": seed_basico["cliente_id"], "items": []})
    assert resp.status_code == 400


def test_venta_requiere_autenticacion(client, seed_basico):
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 1}],
    })
    assert resp.status_code == 401


def test_venta_ignora_total_enviado_por_el_cliente(client, seed_basico):
    """El total SIEMPRE se calcula en el backend, nunca se confía en el
    que mande el cliente (aunque este endpoint ni siquiera lo acepta como
    campo de entrada, verificamos que el total resultante sea el correcto
    según precio x cantidad real en la base de datos)."""
    login(client, **seed_basico["vendedor"])
    resp = client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 1}],
        "total": 0.01,  # intento de manipulación, debe ser ignorado
    })
    assert resp.status_code == 201
    assert resp.get_json()["total"] == 10.0


def test_idempotencia_misma_clave_no_duplica_venta(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    payload = {
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 1}],
    }
    headers = {"Idempotency-Key": "clave-fija-123"}

    resp1 = client.post("/ventas", json=payload, headers=headers)
    resp2 = client.post("/ventas", json=payload, headers=headers)

    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.get_json()["id"] == resp2.get_json()["id"]

    resp = client.get(f"/productos/{seed_basico['producto_a_id']}")
    assert resp.get_json()["stock"] == 4, "El stock solo debe descontarse una vez"

    resp = client.get("/ventas")
    assert len(resp.get_json()) == 1, "Solo debe existir una venta, no dos"


def test_vendedor_solo_ve_sus_propias_ventas(client, app, seed_basico):
    from database.database import get_db
    from services.auth_service import hash_password
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            ("Vendedor Dos", "vendedor2@test.com", hash_password("Vendedor2123!"), "VENDEDOR"),
        )
        db.commit()

    login(client, **seed_basico["vendedor"])
    client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 1}],
    })
    client.post("/auth/logout")

    login(client, "vendedor2@test.com", "Vendedor2123!")
    resp = client.get("/ventas")
    assert resp.get_json() == [], "El segundo vendedor no debe ver ventas del primero"


def test_admin_ve_todas_las_ventas(client, seed_basico):
    login(client, **seed_basico["vendedor"])
    client.post("/ventas", json={
        "cliente_id": seed_basico["cliente_id"],
        "items": [{"producto_id": seed_basico["producto_a_id"], "cantidad": 1}],
    })
    client.post("/auth/logout")

    login(client, **seed_basico["admin"])
    resp = client.get("/ventas")
    assert len(resp.get_json()) == 1


def test_concurrencia_no_vende_mas_stock_del_disponible(app, seed_basico):
    """
    Simula dos clientes comprando al mismo tiempo la última unidad de un
    producto con stock=1. Solo UNA de las dos ventas debe tener éxito;
    la otra debe recibir 409 por falta de stock. El stock final debe ser 0,
    nunca negativo.
    """
    resultados = []

    def comprar():
        with app.test_client() as c:
            login(c, "vendedor@test.com", "Vendedor123!")
            resp = c.post("/ventas", json={
                "cliente_id": seed_basico["cliente_id"],
                "items": [{"producto_id": seed_basico["producto_unico_id"], "cantidad": 1}],
            })
            resultados.append(resp.status_code)

    hilos = [threading.Thread(target=comprar) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert sorted(resultados) == [201, 409], (
        f"Se esperaba exactamente una venta exitosa y una rechazada, se obtuvo: {resultados}"
    )

    with app.app_context():
        from database.database import get_db
        db = get_db()
        row = db.execute(
            "SELECT stock FROM productos WHERE id = ?",
            (seed_basico["producto_unico_id"],),
        ).fetchone()
        assert row["stock"] == 0
