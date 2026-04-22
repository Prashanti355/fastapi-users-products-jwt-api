
`CONTRIBUTING.md`

```markdown
# Contribuir al proyecto

Gracias por querer contribuir.

## Reglas básicas

- No subir secretos, credenciales reales ni archivos `.env`
- Mantener separación por capas: `api`, `schemas`, `services`, `repositories`, `models`, `core`
- Toda nueva funcionalidad relevante debe incluir pruebas
- Si un cambio afecta persistencia, revisar migraciones con Alembic
- Si cambia el comportamiento real del proyecto, actualizar README y `.env.example`

## Flujo recomendado

1. Crear una rama a partir de `main`
2. Implementar el cambio
3. Ejecutar migraciones si aplica
4. Ejecutar pruebas
5. Actualizar documentación si aplica
6. Abrir Pull Request usando la plantilla del repositorio

## Convenciones prácticas

- Endpoints en `app/api/v1/endpoints/`
- Lógica de negocio en `app/services/`
- Acceso a datos en `app/repositories/`
- Configuración, seguridad y middleware en `app/core/`
- DTOs y validaciones en `app/schemas/`

## Comandos útiles

### Levantar entorno con Docker

```bash
docker compose up -d --build