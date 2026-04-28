# Contribuir al proyecto

Gracias por querer contribuir.

## Reglas básicas

- No subir secretos, credenciales reales ni archivos `.env`.
- Mantener la separación por capas: `api`, `schemas`, `services`, `repositories`, `models` y `core`.
- Toda funcionalidad relevante debe incluir pruebas.
- Si un cambio afecta la persistencia, debe revisarse si requiere migración con Alembic.
- Si cambia el comportamiento real del proyecto, deben actualizarse `README.md`, `.env.example` y la documentación operativa correspondiente.
- Antes de abrir un Pull Request, las pruebas deben pasar en local.

## Flujo recomendado

1. Crear una rama a partir de `main`.
2. Implementar el cambio.
3. Crear o revisar migraciones si aplica.
4. Ejecutar pruebas.
5. Actualizar documentación si aplica.
6. Abrir Pull Request usando la plantilla del repositorio.

## Convenciones prácticas

- Endpoints HTTP en `app/api/v1/endpoints/`.
- DTOs y validaciones en `app/schemas/`.
- Lógica de negocio en `app/services/`.
- Acceso a datos en `app/repositories/`.
- Modelos de base de datos en `app/models/`.
- Configuración, seguridad, logging, excepciones y middleware en `app/core/`.
- Scripts manuales de mantenimiento en `app/scripts/`.

## Comandos útiles

### Levantar entorno con Docker

```bash
docker compose up -d --build