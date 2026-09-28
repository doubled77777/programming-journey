# Experimentos

Estos archivos no forman parte del sistema principal (ver `app.py` en la raíz
del proyecto). Se conservan como evidencia del proceso de aprendizaje detrás
de este proyecto, no porque el sistema los use.

| Archivo | Qué es | Por qué ya no se usa |
|---|---|---|
| `sales_system.py` | Primera versión, en consola, con los datos en un diccionario en memoria (sin base de datos) | Reemplazado por una versión con SQLite |
| `main.py` | Segunda versión, en consola, ya con SQLite y roles cliente/administrador | La lógica de negocio (validar stock, registrar ventas) fue reescrita e integrada en `repository.py` para poder usarse desde la API web, no solo desde consola |
| `api_prueba.py` | Práctica consumiendo una API pública (JSONPlaceholder) | Ejercicio de aprendizaje, sin relación directa con el sistema de ventas |
| `api_database.py` | Práctica consumiendo una API pública y guardando resultados en SQLite | Ídem |
| `api_productos.py` | Script que trajo productos de prueba (cosméticos) desde DummyJSON hacia la tabla `productos` | Por eso el catálogo real incluye productos como "Red Lipstick" junto a "Laptop" - quedaron ahí como parte de los datos de prueba |
| `mercadolibre.py` | Práctica consumiendo la API pública de MercadoLibre | Exploración de APIs externas, no relacionada con Mercado Pago |
| `mercadopago_orders_experimento.py` | El primer script que probó la API de Mercado Pago (Orders API) de forma aislada | Su lógica fue reescrita, con manejo de errores y timeouts, en `services/mercadopago_service.py`. Fue clave para descubrir que el proyecto debía usar Orders API y no la clásica Payments API |
| `reporte_automatico.py` | Genera reportes en CSV directamente desde la base de datos | Útil como utilidad de línea de comandos, pero no está conectado a la API web. Candidato natural para convertirse en un endpoint `/reportes` en una futura iteración |

Ninguno de estos scripts se ejecuta como parte de la aplicación Flask. Se
pueden correr de forma independiente (`python experiments/main.py`, etc.)
únicamente con fines de referencia.
