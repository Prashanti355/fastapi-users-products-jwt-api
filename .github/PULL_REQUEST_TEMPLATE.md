## Resumen

Describe aquí, en pocas líneas, qué cambia este PR y por qué.

## Cambios principales

### Backend
- 

### Seguridad
- 

### Persistencia / migraciones
- 

### Documentación
- 

### Pruebas
- 

## Archivos o módulos más importantes tocados

- ``
- ``
- ``

## Validación realizada

Marca lo que sí ejecutaste:

- [ ] `docker compose up -d --build`
- [ ] `docker compose exec api alembic upgrade head`
- [ ] `docker compose exec api pytest tests/unit tests/integration -q`
- [ ] `docker compose exec api pytest tests/unit tests/integration --cov=app --cov-report=term-missing`
- [ ] validación manual en Swagger
- [ ] validación de endpoints sensibles
- [ ] revisión de logs / auditoría si aplica

## Resultado esperado

Explica qué debería observar alguien al probar este cambio.

## Riesgos o puntos de atención

- 
- 

## Checklist final

- [ ] el código corre correctamente
- [ ] las migraciones quedaron alineadas
- [ ] no se subieron secretos ni `.env`
- [ ] el README sigue consistente con el estado real del proyecto
- [ ] los tests relevantes pasan