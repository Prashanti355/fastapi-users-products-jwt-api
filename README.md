# FastAPI Users & Products JWT API

API REST construida con FastAPI para gestión de usuarios y productos, autenticación JWT, PostgreSQL, Docker y versionado de esquema con Alembic.

## Descripción

Este proyecto implementa una API backend desarrollada con FastAPI siguiendo una arquitectura por capas. Incluye módulos de usuarios, productos y autenticación con JWT, control de acceso por roles, documentación interactiva con Swagger, configuración CORS, logs técnicos, logs de auditoría, migraciones con Alembic y pruebas automatizadas.

El desarrollo se realizó de forma incremental. Primero se construyeron los módulos funcionales de usuarios, productos y autenticación. Después se añadieron endurecimientos de seguridad, observabilidad, auditoría, pruebas unitarias e integración, y finalmente se formalizó el control del esquema de base de datos con Alembic para permitir crecimiento y mantenimiento más seguros.

## Características implementadas

### Usuarios

- Alta de usuarios
- Consulta individual y paginada
- Actualización completa y parcial
- Cambio de contraseña
- Activación y desactivación
- Eliminación lógica y restauración
- Restricción de autoedición de campos privilegiados para usuarios normales
- Creación administrativa de usuarios por superusuario

### Productos

- Alta de productos
- Consulta individual y paginada
- Actualización completa y parcial
- Activación y desactivación
- Eliminación lógica y restauración
- Catálogo público sin exponer productos eliminados lógicamente
- Protección de operaciones administrativas para superusuario

### Seguridad

- Registro público de usuarios
- Login con JWT
- Access token y refresh token
- Endpoint `/auth/me`
- Integración con `Authorize` en Swagger
- Protección de endpoints por niveles:
  - público
  - usuario autenticado
  - superusuario
- Endurecimiento del registro público para impedir autoelevación de privilegios
- Restricción de modificación de campos privilegiados para usuarios normales

### Observabilidad

- Configuración CORS con lista explícita de orígenes permitidos
- Logs técnicos persistidos en archivo
- Request ID por petición
- Header `X-Request-ID` en respuestas
- Logs de auditoría persistidos en PostgreSQL
- Correlación entre logs técnicos y auditoría mediante `request_id`

### Migraciones

- Versionado formal del esquema con Alembic
- Migración inicial real para reconstrucción del esquema desde una base vacía
- Flujo de migraciones reproducible con `revision --autogenerate` y `upgrade head`

### Pruebas

- Pruebas unitarias de seguridad, tokens y servicios
- Pruebas de integración para auth, users y products
- Ejecución reproducible dentro de Docker
- Batería automatizada con **98 pruebas aprobadas**

## Tecnologías utilizadas

- Python 3.12
- FastAPI
- SQLModel
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT (`python-jose`)
- bcrypt
- Docker
- Docker Compose
- Swagger / OpenAPI
- pytest
- pytest-asyncio
- httpx
- pytest-mock

## Arquitectura

El proyecto sigue una arquitectura por capas para separar responsabilidades y facilitar el crecimiento del sistema.

- `api/` → endpoints HTTP
- `schemas/` → DTOs y validación de datos
- `services/` → lógica de negocio
- `repositories/` → acceso a datos
- `models/` → entidades de base de datos
- `core/` → configuración, seguridad, logging, base de datos, excepciones y handlers

## Estructura del proyecto

```text
app/
├── api/
│   └── v1/
│       ├── api.py
│       └── endpoints/
│           ├── auth.py
│           ├── products.py
│           └── users.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── logging_config.py
│   ├── request_logging_middleware.py
│   ├── security.py
│   ├── exceptions/
│   └── handlers/
├── models/
│   ├── __init__.py
│   ├── audit_log.py
│   ├── product.py
│   └── user.py
├── repositories/
│   ├── audit_log_repository.py
│   ├── base.py
│   ├── product_repository.py
│   └── user_repository.py
├── schemas/
│   ├── auth.py
│   ├── common.py
│   ├── product.py
│   ├── response.py
│   └── user.py
├── services/
│   ├── audit_log_service.py
│   ├── auth_service.py
│   ├── product_service.py
│   ├── token_service.py
│   └── user_service.py
├── dependencies.py
└── main.py

alembic/
├── env.py
└── versions/

docker/
└── fastapi/
    └── Dockerfile

tests/
├── integration/
│   ├── conftest.py
│   ├── test_auth_endpoints.py
│   ├── test_products_endpoints.py
│   └── test_users_endpoints.py
├── unit/
│   ├── test_auth_service.py
│   ├── test_product_service.py
│   ├── test_security.py
│   ├── test_token_service.py
│   └── test_user_service.py
├── test_connection.py
├── test_db.py
└── test_models.py

docker-compose.yml
alembic.ini
pytest.ini
requirements.txt
requirements-dev.txt
.env.example
README.md
```

## Módulos disponibles

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh-token`
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

## Ejecución con Docker

Esta es la forma recomendada para levantar el proyecto.

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd fastapi-users-products-jwt-api
```

### 2. Crear el archivo `.env`

#### Linux / macOS

```bash
cp .env.example .env
```

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### 3. Levantar servicios

```bash
docker compose up -d --build
```

### 4. Aplicar migraciones

#### Linux / macOS

```bash
docker compose exec api alembic upgrade head
```

#### Windows PowerShell

```powershell
docker compose exec api alembic upgrade head
```

### 5. Verificar contenedores

```bash
docker compose ps
```

### 6. Acceder a la aplicación

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 7. Detener contenedores

```bash
docker compose down
```

## Ejecución local

Aunque el flujo recomendado del proyecto es Docker, también se puede ejecutar localmente.

### 1. Crear entorno virtual

```bash
python -m venv .venv
```

### 2. Activar entorno virtual

#### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Windows CMD

```cmd
.venv\Scripts\activate.bat
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 4. Aplicar migraciones

```bash
alembic upgrade head
```

### 5. Ejecutar la API

```bash
python -m uvicorn app.main:app --reload
```

## Variables de entorno

El proyecto usa variables de entorno para separar configuración sensible del código y evitar hardcodeo.

Variables principales:

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
- `APP_PORT`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `DEFAULT_PAGE_SIZE`
- `MAX_PAGE_SIZE`
- `BACKEND_CORS_ORIGINS`

## Autenticación

La API implementa autenticación basada en JWT con doble token:

- **Access token** para acceso a rutas protegidas
- **Refresh token** para obtener un nuevo par de tokens

### Flujo básico

1. Registrar usuario en `/api/v1/auth/register`
2. Iniciar sesión en `/api/v1/auth/login`
3. Usar el `access_token` para rutas protegidas
4. Refrescar tokens en `/api/v1/auth/refresh-token`
5. Validar el usuario actual en `/api/v1/auth/me`

Swagger permite autenticarse mediante el botón **Authorize**.

## Niveles de acceso

### Público

- Lectura de productos

### Usuario autenticado

- Operaciones protegidas de escritura en productos
- Consulta y actualización del propio usuario
- Cambio de contraseña
- Consulta del usuario autenticado actual

### Superusuario

- Listado completo de usuarios
- Creación administrativa de usuarios
- Activación, desactivación, eliminación y restauración de usuarios
- Activación, desactivación, eliminación y restauración de productos

## CORS

La API incluye configuración CORS con lista explícita de orígenes permitidos.

Se validó:

- preflight `OPTIONS`
- origen permitido
- origen no permitido
- soporte para header `Authorization`
- compatibilidad con rutas públicas y protegidas

## Logs técnicos

La aplicación registra logs técnicos en archivos persistidos fuera del contenedor.

Archivos generados:

- `logs/technical.log`
- `logs/error.log`

Cada request incluye:

- `request_id`
- método HTTP
- ruta
- status code
- latencia
- IP cliente

Además, la API devuelve el header:

- `X-Request-ID`

## Logs de auditoría

La aplicación registra eventos sensibles de negocio en PostgreSQL mediante la tabla:

- `audit_logs`

Eventos auditados actualmente:

- `register`
- `login`
- `refresh_token`
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

Cada registro de auditoría incluye:

- acción
- entidad
- identificador de entidad
- actor
- rol del actor
- `request_id`
- estado
- detalle
- timestamp

## Migraciones con Alembic

El esquema de base de datos está versionado con Alembic.

### Flujo de trabajo

1. Modificar modelos en `app/models/`
2. Generar migración:

```bash
alembic revision --autogenerate -m "descripcion del cambio"
```

3. Revisar manualmente el archivo generado en `alembic/versions/`
4. Aplicar migración:

```bash
alembic upgrade head
```

5. Verificar versión actual:

```bash
alembic current
```

## Pruebas automatizadas

El proyecto incluye:

### Scripts base

- `tests/test_models.py`
- `tests/test_db.py`
- `tests/test_connection.py`

### Pruebas unitarias

- `tests/unit/test_security.py`
- `tests/unit/test_token_service.py`
- `tests/unit/test_auth_service.py`
- `tests/unit/test_user_service.py`
- `tests/unit/test_product_service.py`

### Pruebas de integración

- `tests/integration/test_auth_endpoints.py`
- `tests/integration/test_users_endpoints.py`
- `tests/integration/test_products_endpoints.py`

### Ejecutar toda la batería

```bash
docker compose exec api pytest tests/unit tests/integration -q
```

Resultado actual:

- **98 pruebas aprobadas**

## Estado actual

Hasta este punto, el proyecto ya implementa:

- módulo de usuarios
- módulo de productos
- autenticación y autorización con JWT
- control de acceso por roles
- CORS
- logs técnicos
- logs de auditoría
- migraciones con Alembic
- documentación interactiva
- pruebas unitarias
- pruebas de integración
- despliegue con Docker

## Trabajo siguiente

Las siguientes etapas del proyecto contemplan:

- CI para ejecución automática de pruebas
- cobertura de pruebas
- documentación adicional de endpoints y arquitectura
- endurecimiento adicional de seguridad
- ampliación de módulos de negocio

## Autor

Prashanti Peña Guevara

Proyecto desarrollado como práctica progresiva de backend orientada a construir una API escalable, mantenible y cercana a un entorno real.