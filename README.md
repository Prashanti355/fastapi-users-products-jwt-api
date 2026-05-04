# FastAPI Users, Products & Categories JWT API

API REST desarrollada con FastAPI para gestión de usuarios, productos y categorías, autenticación JWT, control de acceso por roles, auditoría, manejo de sesiones con refresh tokens, recuperación de contraseña, rate limiting, limpieza manual de tokens, migraciones con Alembic, calidad estática con Black/Ruff, CI con GitHub Actions, ejecución con Docker y despliegue en Render.

## Descripción

Este proyecto implementa una API backend con arquitectura por capas, pensada para crecimiento, mantenimiento y validación continua. Incluye módulos de usuarios, productos, categorías y autenticación, documentación interactiva con Swagger, observabilidad mediante logs técnicos, auditoría persistida en PostgreSQL, migraciones reproducibles con Alembic, pruebas automatizadas, control de sesiones del lado del servidor mediante refresh tokens persistidos, rotados y revocables, recuperación de contraseña con envío real de correo y herramientas de calidad estática.

El desarrollo se realizó de forma incremental: primero la lógica de usuarios y productos, después autenticación y autorización, luego observabilidad y auditoría, más tarde la formalización del esquema con Alembic y CI, después el endurecimiento del flujo de sesión con rotación y revocación de refresh tokens, cierre global de sesiones, recuperación de contraseña, rate limiting en endpoints sensibles, limpieza manual de tokens obsoletos, envío real de correos de recuperación, calidad estática y documentación técnica interna. Posteriormente se agregó el módulo de categorías como primer módulo funcional de expansión del catálogo.

El proyecto ya puede tratarse como una base backend escalable para crecer hacia módulos de negocio más completos, como relación producto-categoría, inventario, carrito, órdenes y pagos simulados.

## Demo desplegada

La API se encuentra desplegada públicamente en Render.

- Base URL: `https://fastapi-users-products-jwt-api.onrender.com`
- Swagger UI: `https://fastapi-users-products-jwt-api.onrender.com/docs`
- Health check: `https://fastapi-users-products-jwt-api.onrender.com/health`

## Vista de la documentación interactiva

La API incluye documentación interactiva con Swagger, lo que permite explorar endpoints, probar flujos de autenticación y validar respuestas directamente desde el navegador.

![Swagger UI](docs/images/swagger-ui.png)

## Características principales

### Usuarios

- Alta de usuarios.
- Consulta individual y paginada.
- Actualización completa y parcial.
- Cambio de contraseña.
- Activación y desactivación.
- Eliminación lógica y restauración.
- Restricción de campos privilegiados para usuarios normales.
- Creación administrativa de usuarios por superusuario.

### Productos

- Alta de productos.
- Consulta individual y paginada.
- Actualización completa y parcial.
- Activación y desactivación.
- Eliminación lógica y restauración.
- Catálogo público sin exponer productos eliminados lógicamente.
- Protección de operaciones administrativas para superusuario.

### Categorías

- Alta de categorías.
- Consulta pública de categorías activas.
- Consulta individual por ID.
- Búsqueda por nombre, slug o descripción.
- Slug único y normalizado automáticamente.
- Actualización completa y parcial.
- Activación y desactivación.
- Eliminación lógica y restauración.
- Protección de operaciones administrativas para superusuario.
- Auditoría de operaciones administrativas sobre categorías.

### Seguridad y autenticación

- Registro público.
- Login con JWT.
- Access token y refresh token.
- Endpoint `/api/v1/auth/me`.
- Endpoint `/api/v1/auth/forgot-password`.
- Endpoint `/api/v1/auth/reset-password`.
- Integración con `Authorize` en Swagger.
- Control de acceso por roles:
  - público;
  - usuario autenticado;
  - superusuario.
- Endurecimiento del registro público para impedir autoelevación de privilegios.
- Respuesta neutra en recuperación de contraseña para no exponer si un correo existe o no.

### Gestión de sesiones

- Persistencia de refresh tokens en PostgreSQL.
- Refresh tokens con identificador único (`jti`).
- Rotación de refresh tokens al renovar sesión.
- Revocación explícita de refresh tokens.
- Endpoint `/api/v1/auth/logout`.
- Endpoint `/api/v1/auth/logout-all`.
- Invalidación de refresh tokens revocados.
- Cierre de todas las sesiones activas del usuario autenticado.
- Revocación de sesiones activas tras restablecer contraseña.
- Limpieza manual de tokens expirados o revocados antiguos mediante script.

### Recuperación de contraseña

- Persistencia de `password_reset_tokens` en PostgreSQL.
- Generación de token de recuperación.
- Envío real de correos de recuperación mediante Resend.
- Validación de token válido, no usado y no expirado.
- Marcado del token como usado después del restablecimiento.
- Restablecimiento de contraseña con revocación de refresh tokens activos.
- El backend ya soporta el flujo completo, aunque todavía no existe una interfaz final dedicada para consumir el enlace de recuperación.
- Pruebas funcionales del flujo realizadas sobre el servicio desplegado.

### Protección contra abuso

- Rate limiting configurable por entorno.
- Límite aplicado a `POST /api/v1/auth/login`.
- Límite aplicado a `POST /api/v1/auth/register`.
- Infraestructura preparada para cambiar backend de almacenamiento sin hardcodeo.
- Pruebas de integración para validar respuestas `429 Too Many Requests`.

### Observabilidad y auditoría

- Configuración CORS.
- Logs técnicos en archivo.
- `request_id` por petición.
- Header `X-Request-ID` en respuestas.
- Auditoría persistida en PostgreSQL.
- Endpoint protegido `GET /api/v1/audit-logs`.
- Correlación entre logs técnicos y auditoría mediante `request_id`.
- Auditoría de eventos sensibles como `login`, `refresh_token`, `logout`, `logout_all`, `forgot_password`, `reset_password` y operaciones administrativas sobre usuarios, productos y categorías.

### Migraciones y persistencia

- Esquema versionado con Alembic.
- Migración inicial real para reconstrucción desde base vacía.
- Migración para refresh tokens.
- Migración para tokens de recuperación de contraseña.
- Migración para categorías.
- Flujo reproducible con `revision --autogenerate` y `upgrade head`.
- Arranque del contenedor con migraciones aplicadas antes de iniciar la API.

### Calidad y validación

- Pruebas unitarias.
- Pruebas de integración.
- Ejecución reproducible dentro de Docker.
- CI con GitHub Actions para migraciones, calidad estática y pruebas automáticas.
- Formato automático con Black.
- Análisis estático con Ruff.
- Configuración centralizada de calidad en `pyproject.toml`.
- Validación de cobertura con `pytest-cov`.

## Tecnologías utilizadas

- Python 3.12.
- FastAPI.
- SQLModel.
- SQLAlchemy.
- Alembic.
- PostgreSQL.
- JWT (`python-jose`).
- bcrypt.
- SlowAPI.
- limits.
- Docker.
- Docker Compose.
- Swagger / OpenAPI.
- pytest.
- pytest-asyncio.
- pytest-cov.
- pytest-mock.
- httpx.
- Black.
- Ruff.
- GitHub Actions.
- Render.
- Resend.

## Arquitectura

El proyecto sigue una arquitectura por capas para separar responsabilidades y facilitar la evolución del sistema. La intención es mantener una base backend escalable, donde los endpoints HTTP no concentren lógica de negocio y cada capa tenga una responsabilidad clara.

Flujo general de una petición:

```text
Cliente
  ↓
Endpoint FastAPI
  ↓
Schemas de entrada / salida
  ↓
Dependencias de seguridad y base de datos
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
```

Capas principales:

- `api/` → endpoints HTTP, rutas, dependencias de autorización y coordinación de respuestas.
- `schemas/` → validación de datos, DTOs, contratos de entrada y salida.
- `services/` → lógica de negocio, reglas de operación, coordinación de repositorios y servicios auxiliares.
- `repositories/` → acceso a datos, consultas, persistencia y recuperación de entidades.
- `models/` → entidades persistidas y definición de tablas mediante SQLModel.
- `core/` → configuración, seguridad, JWT, logging, base de datos, manejo de errores, middleware y rate limiting.
- `scripts/` → comandos manuales de mantenimiento.
- `dependencies.py` → ensamblaje de dependencias reutilizables de FastAPI.

La estructura actual se mantiene por capas. Si el proyecto crece con más módulos de negocio, puede migrarse posteriormente a una organización por dominio, por ejemplo:

```text
app/modules/auth/
app/modules/users/
app/modules/products/
app/modules/categories/
app/modules/inventory/
app/modules/cart/
app/modules/orders/
```

Por ahora, los módulos nuevos deben seguir el patrón actual:

```text
model
schema
repository
service
endpoint
migration
tests
documentation
```

La documentación técnica ampliada se encuentra en:

- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/TESTING.md`
- `docs/PERMISSIONS.md`

## Estructura del proyecto

```text
app/
├── api/
│   └── v1/
│       ├── api.py
│       └── endpoints/
│           ├── audit_logs.py
│           ├── auth.py
│           ├── categories.py
│           ├── products.py
│           └── users.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── logging_config.py
│   ├── rate_limit.py
│   ├── request_logging_middleware.py
│   ├── security.py
│   ├── exceptions/
│   │   ├── auth_exceptions.py
│   │   ├── base.py
│   │   ├── category_exceptions.py
│   │   ├── common.py
│   │   ├── product_exceptions.py
│   │   └── user_exceptions.py
│   └── handlers/
├── models/
│   ├── __init__.py
│   ├── audit_log.py
│   ├── category.py
│   ├── password_reset_token.py
│   ├── product.py
│   ├── refresh_token.py
│   └── user.py
├── repositories/
│   ├── audit_log_repository.py
│   ├── base.py
│   ├── category_repository.py
│   ├── password_reset_token_repository.py
│   ├── product_repository.py
│   ├── refresh_token_repository.py
│   └── user_repository.py
├── schemas/
│   ├── audit_log.py
│   ├── auth.py
│   ├── category.py
│   ├── common.py
│   ├── product.py
│   ├── response.py
│   └── user.py
├── scripts/
│   ├── __init__.py
│   └── cleanup_refresh_tokens.py
├── services/
│   ├── __init__.py
│   ├── audit_log_service.py
│   ├── auth_service.py
│   ├── category_service.py
│   ├── email_service.py
│   ├── password_reset_token_service.py
│   ├── product_service.py
│   ├── refresh_token_service.py
│   ├── token_service.py
│   └── user_service.py
├── dependencies.py
└── main.py

alembic/
├── env.py
└── versions/
    ├── 16472867c38c_create_initial_schema.py
    ├── ae8ddeebea92_add_refresh_tokens_table.py
    ├── b3f4e1c8a901_add_password_reset_tokens_table.py
    ├── c9a2f7d41b10_make_password_reset_token_timestamps_timezone_aware.py
    └── 40ed006f73c5_add_categories_table.py

docker/
└── fastapi/
    └── Dockerfile

.github/
├── workflows/
│   └── ci.yml
└── PULL_REQUEST_TEMPLATE.md

docs/
├── ARCHITECTURE.md
├── DEPLOY_CHECKLIST.md
├── PERMISSIONS.md
├── QUICKSTART.md
├── SECURITY.md
├── TESTING.md
├── images/
│   └── swagger-ui.png
└── postman/
    ├── FastAPI_Users_Products_API.postman_collection.json
    └── FastAPI_Users_Products_API.local_environment.json

tests/
├── integration/
│   ├── test_audit_log_repository.py
│   ├── test_audit_logs_endpoints.py
│   ├── test_auth_endpoints.py
│   ├── test_base_repository.py
│   ├── test_categories_endpoints.py
│   ├── test_category_repository.py
│   ├── test_password_reset_token_service.py
│   ├── test_product_repository.py
│   ├── test_products_endpoints.py
│   ├── test_refresh_token_cleanup.py
│   ├── test_refresh_token_repository.py
│   ├── test_user_repository.py
│   └── test_users_endpoints.py
├── unit/
│   ├── test_audit_log_service.py
│   ├── test_audit_logs_endpoints_unit.py
│   ├── test_auth_endpoints_unit.py
│   ├── test_auth_exceptions.py
│   ├── test_auth_service.py
│   ├── test_categories_endpoints_unit.py
│   ├── test_category_service.py
│   ├── test_cleanup_refresh_tokens_script.py
│   ├── test_common_exceptions.py
│   ├── test_common_schemas.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_email_service.py
│   ├── test_exception_handlers.py
│   ├── test_main.py
│   ├── test_product_service.py
│   ├── test_products_endpoints_unit.py
│   ├── test_rate_limit.py
│   ├── test_refresh_token_service.py
│   ├── test_request_logging_middleware.py
│   ├── test_security.py
│   ├── test_token_service.py
│   ├── test_user_exceptions.py
│   ├── test_user_model.py
│   ├── test_user_service.py
│   └── test_users_endpoints_unit.py
├── test_connection.py
├── test_db.py
└── test_models.py

docker-compose.yml
alembic.ini
pytest.ini
pyproject.toml
requirements.txt
requirements-dev.txt
.env.example
.gitignore
CONTRIBUTING.md
LICENSE
README.md
```

## Endpoints principales

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh-token`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/logout-all`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `GET /api/v1/auth/me`

### Users

- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `POST /api/v1/users`
- `PUT /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `POST /api/v1/users/{user_id}/change-password`
- `PATCH /api/v1/users/{user_id}/activate`
- `PATCH /api/v1/users/{user_id}/deactivate`
- `DELETE /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}/restore`

### Products

- `GET /api/v1/products`
- `GET /api/v1/products/{id}`
- `POST /api/v1/products`
- `PUT /api/v1/products/{id}`
- `PATCH /api/v1/products/{id}`
- `PATCH /api/v1/products/{id}/activate`
- `PATCH /api/v1/products/{id}/deactivate`
- `DELETE /api/v1/products/{id}`
- `PATCH /api/v1/products/{id}/restore`

### Categories

- `GET /api/v1/categories`
- `GET /api/v1/categories/{category_id}`
- `POST /api/v1/categories`
- `PUT /api/v1/categories/{category_id}`
- `PATCH /api/v1/categories/{category_id}`
- `PATCH /api/v1/categories/{category_id}/activate`
- `PATCH /api/v1/categories/{category_id}/deactivate`
- `DELETE /api/v1/categories/{category_id}`
- `PATCH /api/v1/categories/{category_id}/restore`

### Audit Logs

- `GET /api/v1/audit-logs`

## Ejecución con Docker

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd fastapi-users-products-jwt-api
```

### 2. Crear el archivo `.env`

En Linux o macOS:

```bash
cp .env.example .env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

### 3. Levantar servicios

```bash
docker compose up -d --build
```

La configuración actual ejecuta las migraciones con Alembic antes de iniciar la aplicación dentro del contenedor.

### 4. Ver logs de la API

```bash
docker compose logs -f api
```

Para salir de los logs, usar `Ctrl + C`. Esto no detiene los contenedores.

### 5. Acceder a la API

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Nota sobre PostgreSQL 18 y Docker

El proyecto usa `postgres:18-alpine`. Para esta versión, el volumen de PostgreSQL se monta en:

```text
/var/lib/postgresql
```

Esto evita el error de inicialización asociado con montar el volumen directamente en `/var/lib/postgresql/data` en imágenes PostgreSQL 18+.

Si la base local queda en un estado inconsistente durante pruebas o cambios de migraciones, puede reconstruirse desde cero con:

```bash
docker compose down -v
docker compose up -d --build
```

## Despliegue en Render

El proyecto puede desplegarse en Render usando una base PostgreSQL gestionada y un Web Service basado en Docker.

Valores importantes usados en producción:

- `DATABASE_URL` configurada desde la base PostgreSQL de Render.
- `ENVIRONMENT=production`.
- `DEBUG=False`.
- `PORT=10000`.
- `RESEND_API_KEY`.
- `EMAIL_FROM`.
- `FRONTEND_RESET_PASSWORD_URL`.

URL pública actual:

- `https://fastapi-users-products-jwt-api.onrender.com`

## Ejecución local sin Docker

El flujo recomendado es Docker Compose. La ejecución local directa solo debe usarse si se tiene PostgreSQL configurado y las variables de entorno correctas.

```bash
python -m venv .venv
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

## Variables de entorno principales

- `PROJECT_NAME`
- `VERSION`
- `DEBUG`
- `ENVIRONMENT`
- `API_V1_STR`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_URL`
- `APP_PORT`
- `PORT`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `DEFAULT_PAGE_SIZE`
- `MAX_PAGE_SIZE`
- `BACKEND_CORS_ORIGINS`
- `LOG_DIR`
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_STORAGE_URI`
- `RATE_LIMIT_HEADERS_ENABLED`
- `RATE_LIMIT_DEFAULTS`
- `RATE_LIMIT_LOGIN`
- `RATE_LIMIT_REGISTER`
- `RESEND_API_KEY`
- `EMAIL_FROM`
- `FRONTEND_RESET_PASSWORD_URL`

## Logs técnicos

La aplicación genera:

- `logs/technical.log`
- `logs/error.log`

Cada request registra, entre otros datos:

- `request_id`
- método HTTP
- ruta
- status code
- latencia
- IP cliente

## Logs de auditoría

La tabla `audit_logs` registra eventos sensibles como:

- `register`
- `login`
- `refresh_token`
- `logout`
- `logout_all`
- `forgot_password`
- `reset_password`
- `create_user`
- `update_user`
- `partial_update_user`
- `change_password`
- `activate_user`
- `deactivate_user`
- `delete_user`
- `restore_user`
- `create_product`
- `update_product`
- `partial_update_product`
- `activate_product`
- `deactivate_product`
- `delete_product`
- `restore_product`
- `create_category`
- `update_category`
- `partial_update_category`
- `activate_category`
- `deactivate_category`
- `delete_category`
- `restore_category`

Cada evento conserva acción, entidad, actor, rol, `request_id`, estado, detalle y fecha.

## Migraciones con Alembic

Flujo de trabajo:

```bash
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
alembic current
```

Dentro de Docker:

```bash
docker compose exec api alembic revision --autogenerate -m "descripcion del cambio"
docker compose exec api alembic upgrade head
docker compose exec api alembic current
```

Migración actual de categorías:

```text
40ed006f73c5_add_categories_table.py
```

## Limpieza manual de refresh tokens

El proyecto incluye un script para borrar refresh tokens expirados o revocados antiguos.

Ejecución básica:

```bash
docker compose exec api python -m app.scripts.cleanup_refresh_tokens
```

Con antigüedad personalizada para tokens revocados:

```bash
docker compose exec api python -m app.scripts.cleanup_refresh_tokens --revoked-older-than-days 15
```

El script elimina:

- refresh tokens expirados;
- refresh tokens revocados hace más de `N` días.

## Pruebas

Ejecutar toda la batería:

```bash
docker compose exec api pytest tests/unit tests/integration -q
```

Con reporte de cobertura:

```bash
docker compose exec api pytest tests/unit tests/integration --cov=app --cov-report=term-missing
```

Validar formato con Black:

```bash
docker compose exec api black --check app tests
```

Validar análisis estático con Ruff:

```bash
docker compose exec api ruff check app tests
```

Aplicar formato automático:

```bash
docker compose exec api black app tests
```

Aplicar correcciones automáticas seguras de Ruff:

```bash
docker compose exec api ruff check app tests --fix
```

Pruebas específicas del módulo de categorías:

```bash
docker compose exec api pytest tests/unit/test_category_service.py -q
docker compose exec api pytest tests/unit/test_categories_endpoints_unit.py -q
docker compose exec api pytest tests/integration/test_category_repository.py -q
docker compose exec api pytest tests/integration/test_categories_endpoints.py -q
```

## Documentación operativa y técnica

Además del README, el repositorio incluye:

- `CONTRIBUTING.md` para reglas básicas de colaboración.
- `docs/QUICKSTART.md` para arranque rápido del proyecto.
- `docs/DEPLOY_CHECKLIST.md` para validación previa a despliegue.
- `docs/ARCHITECTURE.md` para explicar la arquitectura por capas y el flujo interno de una petición.
- `docs/SECURITY.md` para documentar autenticación, autorización, refresh tokens, recuperación de contraseña, auditoría, CORS y secretos.
- `docs/TESTING.md` para describir pruebas unitarias, integración, cobertura, Black, Ruff y CI.
- `docs/PERMISSIONS.md` para definir la matriz de permisos actual y criterios de autorización para módulos futuros.
- `.github/PULL_REQUEST_TEMPLATE.md` para estandarizar futuros Pull Requests.
- Colección y environment de Postman en `docs/postman/`.

## CI

El proyecto incluye un workflow de GitHub Actions para:

- instalar dependencias;
- levantar PostgreSQL en CI;
- ejecutar migraciones con Alembic;
- verificar el esquema resultante;
- validar formato con Black;
- ejecutar análisis estático con Ruff;
- correr pruebas unitarias e integración;
- generar reporte de cobertura;
- reducir corridas duplicadas con control de concurrencia.

El CI debe pasar antes de fusionar cambios en `main`.

## Licencia

Este proyecto se distribuye bajo licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## Estado del proyecto

El proyecto se encuentra en un estado funcional y consolidado. La base principal del backend ya está implementada, cubierta con pruebas automatizadas, desplegada públicamente y documentada.

Actualmente incluye autenticación JWT, refresh tokens persistidos, recuperación de contraseña con envío real de correo, auditoría, rate limiting, migraciones con Alembic, ejecución con Docker, CI con GitHub Actions, calidad estática con Black/Ruff, documentación técnica interna y el módulo de categorías como primera expansión funcional del catálogo.

El proyecto ya puede tratarse como una base backend escalable para crecer hacia módulos de negocio más completos.

## Siguientes pasos

- Relacionar productos con categorías mediante `category_id`.
- Agregar filtros de productos por categoría.
- Actualizar Postman con los endpoints de categorías.
- Agregar módulo de inventario.
- Agregar carrito de compras.
- Agregar órdenes y detalle de órdenes.
- Definir flujo de pagos simulados.
- Mantener actualizada la matriz de permisos por cada módulo nuevo.
- Evaluar modularización por dominio cuando el número de módulos crezca.
- Crear una interfaz dedicada para consumir el enlace de recuperación de contraseña.

## Autor

Prashanti Peña Guevara

Proyecto backend orientado a construir una API escalable y mantenible.