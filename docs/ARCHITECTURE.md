# Arquitectura

Este documento describe la organización técnica de la API, el flujo general de una petición y los criterios que deben mantenerse al expandir el proyecto.

## 1. Visión general

El proyecto implementa una API REST con FastAPI, PostgreSQL, SQLModel/SQLAlchemy y Alembic. La estructura actual sigue una arquitectura por capas, diseñada para separar responsabilidades y facilitar el crecimiento del backend.

La API incluye actualmente:

- gestión de usuarios;
- gestión de productos;
- autenticación con JWT;
- refresh tokens persistidos;
- recuperación de contraseña;
- control de acceso por roles;
- auditoría persistida;
- rate limiting;
- migraciones con Alembic;
- pruebas automatizadas;
- ejecución con Docker Compose;
- CI con GitHub Actions.

La intención del proyecto es funcionar como una base backend escalable. Los próximos módulos deben agregarse conservando la separación entre endpoints, schemas, servicios, repositorios y modelos.

## 2. Capas principales

La estructura principal se organiza así:

```text
app/
├── api/
├── core/
├── models/
├── repositories/
├── schemas/
├── scripts/
├── services/
├── dependencies.py
└── main.py
```

## 3. Responsabilidad de cada capa

### `app/api/`

Contiene la definición de endpoints HTTP. Esta capa recibe solicitudes, aplica dependencias de autorización, valida entradas mediante schemas y delega la lógica al servicio correspondiente.

Los endpoints no deben concentrar reglas de negocio complejas. Su función principal es coordinar la entrada y salida HTTP.

Ejemplo de responsabilidades:

- declarar rutas;
- recibir parámetros;
- aplicar `Depends`;
- devolver respuestas estructuradas;
- invocar servicios;
- registrar auditoría cuando aplique.

### `app/schemas/`

Contiene modelos Pydantic para entrada, salida y respuestas comunes.

Esta capa define:

- payloads de creación;
- payloads de actualización;
- respuestas públicas;
- respuestas paginadas;
- validaciones de campos;
- contratos de datos expuestos por la API.

Los schemas deben evitar exponer campos internos o sensibles.

### `app/services/`

Contiene la lógica de negocio.

Esta capa decide qué puede o no puede hacerse. Debe concentrar reglas como:

- validar existencia de entidades;
- impedir operaciones inválidas;
- coordinar repositorios;
- aplicar reglas de autenticación o sesión;
- generar tokens;
- revocar sesiones;
- preparar respuestas de dominio.

Los servicios no deben depender directamente de detalles HTTP.

### `app/repositories/`

Contiene acceso a base de datos.

Esta capa encapsula consultas, inserciones, actualizaciones y borrados. Los servicios deben usar repositorios en lugar de escribir consultas directamente.

Ejemplo de responsabilidades:

- buscar por ID;
- buscar por email;
- listar con filtros;
- persistir entidades;
- eliminar lógicamente;
- recuperar tokens;
- consultar logs de auditoría.

### `app/models/`

Contiene entidades persistidas mediante SQLModel.

Esta capa representa la estructura de tablas y relaciones de base de datos. Los cambios en modelos persistidos deben revisarse junto con Alembic.

### `app/core/`

Contiene elementos transversales:

- configuración;
- conexión a base de datos;
- seguridad;
- JWT;
- logging;
- rate limiting;
- excepciones;
- handlers globales;
- middleware de request logging.

Esta capa debe mantenerse estable, porque es usada por varios módulos.

### `app/scripts/`

Contiene scripts manuales de mantenimiento.

Actualmente incluye limpieza de refresh tokens expirados o revocados antiguos.

Los scripts no deben ejecutarse automáticamente en producción salvo que exista una decisión explícita.

### `app/dependencies.py`

Centraliza dependencias reutilizables de FastAPI:

- repositorios;
- servicios;
- usuario autenticado;
- superusuario;
- token OAuth2;
- `request_id`.

Esto evita duplicar ensamblaje de dependencias en cada endpoint.

## 4. Flujo general de una petición

El flujo típico de una petición es:

```text
Cliente
  ↓
FastAPI endpoint
  ↓
Schema de entrada
  ↓
Dependencias de seguridad / base de datos
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
  ↓
Repository
  ↓
Service
  ↓
Schema de respuesta
  ↓
Cliente
```

Ejemplo conceptual:

```text
POST /api/v1/products
  ↓
ProductCreateRequest
  ↓
get_current_active_user
  ↓
ProductService.create_product()
  ↓
ProductRepository.create()
  ↓
PostgreSQL
  ↓
ApiResponse[ProductResponse]
```

## 5. Persistencia y migraciones

La base de datos usa PostgreSQL. El esquema se controla mediante Alembic.

La regla del proyecto es:

```text
Alembic es la fuente de verdad para crear y modificar el esquema de base de datos.
```

No debe usarse `SQLModel.metadata.create_all()` como mecanismo principal de creación de tablas en ejecución normal.

Cuando se modifique un modelo persistido, debe revisarse si corresponde generar una migración:

```bash
docker compose exec api alembic revision --autogenerate -m "descripcion del cambio"
```

Después, la migración debe revisarse manualmente antes de aplicarse:

```bash
docker compose exec api alembic upgrade head
```

## 6. Respuestas de la API

La API usa respuestas estructuradas mediante schemas comunes.

El objetivo es que los endpoints mantengan un formato consistente en operaciones exitosas y errores controlados.

Cuando se agreguen módulos nuevos, deben conservarse estos criterios:

- respuestas claras;
- mensajes consistentes;
- códigos HTTP adecuados;
- errores controlados mediante excepciones propias;
- no exponer detalles internos innecesarios.

## 7. Auditoría

Los eventos sensibles deben registrarse en `audit_logs`.

Actualmente se auditan eventos relacionados con:

- autenticación;
- refresh tokens;
- logout;
- recuperación de contraseña;
- operaciones administrativas sobre usuarios;
- operaciones administrativas sobre productos.

Cuando se agreguen módulos nuevos, deben auditarse eventos sensibles como:

- creación de órdenes;
- cancelación de órdenes;
- cambios de inventario;
- operaciones administrativas;
- cambios de estado relevantes;
- acciones que afecten seguridad o datos críticos.

## 8. Rate limiting

El rate limiting protege endpoints sensibles, principalmente autenticación y registro.

La configuración se controla por variables de entorno. En desarrollo puede usarse un límite amplio. En testing/CI puede usarse un límite más bajo para que las pruebas de `429 Too Many Requests` sean determinísticas.

## 9. Criterios para agregar nuevos módulos

Cada nuevo módulo debe seguir el patrón actual:

```text
model
schema
repository
service
endpoint
migration
tests
documentation
audit logs, si aplica
```

Por ejemplo, un módulo `categories` debería incluir:

```text
app/models/category.py
app/schemas/category.py
app/repositories/category_repository.py
app/services/category_service.py
app/api/v1/endpoints/categories.py
alembic/versions/<revision>_add_categories_table.py
tests/unit/test_category_service.py
tests/unit/test_categories_endpoints_unit.py
tests/integration/test_category_repository.py
tests/integration/test_categories_endpoints.py
```

## 10. Estructura actual vs. estructura futura

La estructura actual por capas es adecuada para la fase actual del proyecto.

Si el backend crece con varios módulos de negocio, puede evaluarse una migración a estructura modular por dominio:

```text
app/
├── modules/
│   ├── auth/
│   ├── users/
│   ├── products/
│   ├── categories/
│   ├── inventory/
│   ├── carts/
│   └── orders/
├── core/
└── main.py
```

Esa migración no es necesaria todavía. Primero conviene expandir uno o dos módulos manteniendo la arquitectura actual. Si la cantidad de archivos por capa empieza a dificultar el mantenimiento, se podrá modularizar por dominio.

## 11. Reglas de mantenimiento

Antes de fusionar cambios en `main`, deben pasar:

```bash
docker compose exec api black --check app tests
docker compose exec api ruff check app tests
docker compose exec api pytest tests/unit tests/integration -q
```

Si el cambio toca persistencia, también debe verificarse:

```bash
docker compose exec api alembic current
docker compose exec api alembic upgrade head
```

La expansión del proyecto debe priorizar estabilidad, pruebas y claridad arquitectónica.