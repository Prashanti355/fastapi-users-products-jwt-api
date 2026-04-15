# FastAPI Users & Products JWT API

API REST con FastAPI para gestión de usuarios y productos, autenticación JWT, PostgreSQL y Docker.

## Descripción

Este proyecto implementa una API backend desarrollada con FastAPI siguiendo una arquitectura por capas. Actualmente incluye módulos de usuarios, productos y autenticación con JWT, además de control de acceso por roles, documentación interactiva con Swagger, configuración CORS, logs técnicos, logs de auditoría y pruebas automatizadas.

El proyecto fue construido de forma incremental, comenzando por el manejo de usuarios, después productos y finalmente autenticación y autorización. Posteriormente se añadieron endurecimientos de seguridad, pruebas unitarias e integración, observabilidad técnica y auditoría de eventos sensibles.

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

- Configuración CORS para orígenes permitidos
- Logs técnicos persistidos en archivo
- Request ID por petición
- Header `X-Request-ID` en respuestas
- Logs de auditoría persistidos en PostgreSQL para eventos sensibles

### Pruebas

- Pruebas unitarias de seguridad, tokens y servicios
- Pruebas de integración para auth, users y products
- Ejecución reproducible dentro de Docker
- Batería automatizada con 98 pruebas exitosas

## Tecnologías utilizadas

- Python 3.12
- FastAPI
- SQLModel
- SQLAlchemy
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
- `core/` → configuración, seguridad, logging, excepciones y handlers

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
logs/
docker-compose.yml
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

Copia el archivo `.env.example` y crea tu configuración real.

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

### 4. Verificar contenedores

```bash
docker compose ps
```

### 5. Acceder a la aplicación

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 6. Detener contenedores

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

### 4. Ejecutar la API

```bash
python -m uvicorn app.main:app --reload
```

## Variables de entorno

El proyecto usa variables de entorno para evitar hardcodeo y separar configuración sensible del código.

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

## Archivo `.env.example`

El proyecto incluye un `.env.example` como plantilla segura de configuración.

El archivo `.env` real no debe subirse al repositorio.

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

Swagger permite autenticarse usando el botón **Authorize**.

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

Se valida:

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
- estado
- detalle
- timestamp

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
docker compose exec api pytest tests/unit tests/integration -v
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
- documentación interactiva
- pruebas unitarias
- pruebas de integración
- despliegue con Docker

## Trabajo siguiente

Las siguientes etapas del proyecto contemplan:

- migraciones formales con Alembic
- CI para ejecución automática de pruebas
- cobertura de pruebas
- documentación adicional de endpoints y arquitectura
- mejoras adicionales de observabilidad y seguridad

## Autor

Prashanti Peña Guevara

Proyecto desarrollado como práctica progresiva de backend orientada a construir una API escalable, bien estructurada y cercana a un entorno real.
