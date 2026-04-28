# Testing

Este documento describe cómo se validan los cambios del proyecto, qué tipos de pruebas existen y qué comandos deben ejecutarse antes de abrir o fusionar un Pull Request.

## 1. Visión general

El proyecto cuenta con pruebas unitarias e integración para validar:

- configuración;
- seguridad;
- autenticación;
- refresh tokens;
- recuperación de contraseña;
- usuarios;
- productos;
- auditoría;
- repositorios;
- servicios;
- endpoints;
- rate limiting;
- scripts de mantenimiento;
- manejo de errores;
- middleware de logging.

El objetivo es que cada cambio importante pueda validarse de forma reproducible dentro de Docker.

## 2. Ejecución recomendada

El flujo recomendado de validación local es:

```bash
docker compose up -d --build
docker compose exec api alembic current
docker compose exec api black --check app tests
docker compose exec api ruff check app tests
docker compose exec api pytest tests/unit tests/integration -q
docker compose exec api pytest tests/unit tests/integration --cov=app --cov-report=term-missing
```

## 3. Pruebas unitarias

Las pruebas unitarias se encuentran en:

```text
tests/unit/
```

Estas pruebas validan componentes de forma aislada.

Ejemplos:

- servicios;
- excepciones;
- schemas;
- funciones de seguridad;
- endpoints con dependencias simuladas;
- scripts;
- configuración;
- middleware.

Ejecutar solo pruebas unitarias:

```bash
docker compose exec api pytest tests/unit -q
```

## 4. Pruebas de integración

Las pruebas de integración se encuentran en:

```text
tests/integration/
```

Estas pruebas validan interacción real entre componentes, incluyendo base de datos de prueba cuando aplica.

Ejemplos:

- repositorios;
- endpoints completos;
- flujos de autenticación;
- refresh tokens;
- auditoría;
- productos;
- usuarios;
- recuperación de contraseña;
- rate limiting.

Ejecutar solo pruebas de integración:

```bash
docker compose exec api pytest tests/integration -q
```

## 5. Batería completa

Ejecutar toda la batería:

```bash
docker compose exec api pytest tests/unit tests/integration -q
```

Estado actual esperado:

```text
337 passed
```

## 6. Cobertura

Ejecutar cobertura:

```bash
docker compose exec api pytest tests/unit tests/integration --cov=app --cov-report=term-missing
```

Estado actual esperado:

```text
98% coverage
```

La cobertura debe usarse como indicador de apoyo. No sustituye la revisión de calidad de las pruebas.

## 7. Black

Black se usa para formato automático.

Aplicar formato:

```bash
docker compose exec api black app tests
```

Verificar formato sin modificar archivos:

```bash
docker compose exec api black --check app tests
```

La verificación con `--check` debe pasar antes de abrir un PR.

## 8. Ruff

Ruff se usa para análisis estático y limpieza de código.

Aplicar correcciones automáticas seguras:

```bash
docker compose exec api ruff check app tests --fix
```

Verificar sin modificar archivos:

```bash
docker compose exec api ruff check app tests
```

La configuración está en:

```text
pyproject.toml
```

Ruff está ajustado para convivir con patrones normales de FastAPI, como `Depends`, `Query`, `Path` y `Body` en parámetros de endpoints.

## 9. Migraciones en pruebas

Antes de correr pruebas de integración en un entorno limpio, debe aplicarse Alembic:

```bash
docker compose exec api alembic upgrade head
```

Verificar migración actual:

```bash
docker compose exec api alembic current
```

El resultado esperado debe indicar la revisión marcada como `head`.

## 10. CI con GitHub Actions

El workflow de CI ejecuta:

- checkout del repositorio;
- instalación de Python;
- instalación de dependencias;
- arranque de PostgreSQL;
- migraciones con Alembic;
- verificación de tablas principales;
- Black en modo check;
- Ruff;
- pruebas unitarias e integración;
- cobertura.

El CI debe pasar antes de fusionar cambios en `main`.

## 11. Rate limiting en pruebas

Las pruebas de rate limiting validan que endpoints sensibles puedan devolver:

```text
429 Too Many Requests
```

En CI pueden usarse límites más bajos para que estas pruebas sean determinísticas y no dependan de la velocidad de GitHub Actions.

Ejemplo:

```env
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=5/minute
```

En desarrollo local pueden usarse límites más amplios.

## 12. Pruebas de endpoints

Los endpoints deben probarse en dos niveles cuando sea necesario:

```text
unitarias → validan el endpoint con dependencias simuladas
integración → validan el flujo completo con base de datos
```

Cuando se agregue un endpoint nuevo, debe incluirse al menos:

- caso exitoso;
- recurso inexistente si aplica;
- validación de permisos;
- validación de datos inválidos;
- auditoría si aplica.

## 13. Pruebas de servicios

Los servicios concentran reglas de negocio. Por eso deben probarse con mayor detalle.

Cuando se agregue una regla nueva, debe cubrirse:

- flujo exitoso;
- error esperado;
- caso límite;
- interacción con repositorios;
- interacción con otros servicios si aplica.

## 14. Pruebas de repositorios

Los repositorios deben validarse mediante pruebas de integración, porque dependen del comportamiento real de base de datos.

Deben cubrirse casos como:

- crear registros;
- buscar por ID;
- buscar por campo único;
- listar con filtros;
- actualizar;
- eliminar;
- restaurar, si aplica;
- respetar restricciones de base de datos.

## 15. Pruebas de seguridad

Los flujos sensibles deben tener pruebas explícitas:

- login correcto;
- login incorrecto;
- access token válido;
- access token inválido;
- refresh token válido;
- refresh token revocado;
- logout;
- logout global;
- recuperación de contraseña;
- cambio de contraseña;
- acceso de usuario normal a recurso restringido;
- acceso de superusuario.

## 16. Pruebas para nuevos módulos

Cada nuevo módulo debe incluir, como mínimo:

```text
tests/unit/test_<module>_service.py
tests/unit/test_<module>_endpoints_unit.py
tests/integration/test_<module>_repository.py
tests/integration/test_<module>_endpoints.py
```

Si el módulo requiere auditoría, también deben agregarse pruebas que verifiquen creación de eventos.

Si el módulo modifica datos críticos, deben incluirse casos de consistencia y transacciones.

## 17. Validación manual

Además de pruebas automatizadas, algunos cambios pueden requerir validación manual en Swagger o Postman.

Ejemplos:

- login desde Swagger;
- botón `Authorize`;
- creación de usuario;
- recuperación de contraseña;
- creación de producto;
- consulta de audit logs;
- flujo de refresh token;
- logout;
- logout global.

La validación manual debe mencionarse en la descripción del Pull Request cuando aplique.

## 18. Criterio mínimo antes de PR

Antes de abrir un PR, ejecutar:

```bash
docker compose exec api black --check app tests
docker compose exec api ruff check app tests
docker compose exec api pytest tests/unit tests/integration -q
```

Si el cambio toca base de datos:

```bash
docker compose exec api alembic current
docker compose exec api alembic upgrade head
```

Si el cambio es amplio o toca lógica crítica:

```bash
docker compose exec api pytest tests/unit tests/integration --cov=app --cov-report=term-missing
```

## 19. Criterio mínimo antes de merge

Antes de fusionar en `main`, debe cumplirse:

```text
Black pasa
Ruff pasa
Pytest pasa
CI pasa en GitHub Actions
no hay secretos versionados
no hay .env en el commit
las migraciones están alineadas
la documentación se actualizó si el comportamiento cambió
```

## 20. Interpretación del número de pruebas

El número de pruebas puede cambiar cuando se agregan nuevos casos o cuando se corrige un nombre duplicado que impedía que Pytest descubriera una prueba.

El número actual esperado es:

```text
337 pruebas aprobadas
```

Si el número cambia, debe actualizarse la documentación que haga referencia explícita al total.