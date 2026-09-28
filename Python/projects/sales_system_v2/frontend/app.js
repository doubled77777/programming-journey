// Helper compartido para consumir la API Flask desde todas las páginas.
// Usa 'credentials: include' porque la autenticación es por cookie de
// sesión (no por token en localStorage), así que el navegador debe
// enviar la cookie en cada request.

const API_BASE = '';

async function api(path, method = 'GET', body = null, idempotencyKey = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey;

    const resp = await fetch(API_BASE + path, {
        method,
        headers,
        credentials: 'include',
        body: body ? JSON.stringify(body) : undefined,
    });

    let data = null;
    try {
        data = await resp.json();
    } catch (e) {
        data = null;
    }

    if (!resp.ok) {
        const mensaje = (data && data.error) ? data.error : `Error ${resp.status}`;
        throw new Error(mensaje);
    }
    return data;
}

function getUsuario() {
    const raw = localStorage.getItem('usuario');
    return raw ? JSON.parse(raw) : null;
}

function requireLogin() {
    if (!getUsuario()) {
        window.location.href = 'login.html';
    }
}
