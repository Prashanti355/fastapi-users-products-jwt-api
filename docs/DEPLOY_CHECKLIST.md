# Checklist de despliegue

## 1. Verificaciones previas

- [ ] La rama está actualizada
- [ ] El README refleja el estado real del proyecto
- [ ] `.env.example` está completo y actualizado
- [ ] `.gitignore` protege secretos, logs y artefactos locales
- [ ] No hay archivos sensibles pendientes en `git status`

## 2. Validación técnica local

- [ ] La aplicación levanta con Docker
- [ ] PostgreSQL inicia correctamente
- [ ] Alembic aplica migraciones sin errores
- [ ] Swagger está disponible
- [ ] El endpoint `/health` responde correctamente

## 3. Pruebas

- [ ] Pruebas unitarias aprobadas
- [ ] Pruebas de integración aprobadas
- [ ] Cobertura revisada
- [ ] Endpoints críticos probados manualmente:
  - [ ] register
  - [ ] login
  - [ ] refresh-token
  - [ ] logout
  - [ ] logout-all
  - [ ] forgot-password
  - [ ] reset-password
  - [ ] users
  - [ ] products
  - [ ] audit-logs

## 4. Seguridad

- [ ] `SECRET_KEY` real y segura en el entorno de despliegue
- [ ] `DEBUG=False`
- [ ] Credenciales reales fuera del repositorio
- [ ] Variables sensibles solo en entorno seguro
- [ ] Rate limit revisado para el entorno objetivo
- [ ] CORS revisado para el frontend real

## 5. Base de datos

- [ ] La cadena de conexión es correcta
- [ ] La base existe
- [ ] Las migraciones están alineadas con los modelos actuales
- [ ] No hay drift entre código y esquema
- [ ] La estrategia de rollback está clara si algo falla

## 6. Observabilidad

- [ ] Logging técnico habilitado
- [ ] Logging de errores habilitado
- [ ] `request_id` presente en respuestas
- [ ] Auditoría funcionando en eventos sensibles
- [ ] Health check operativo

## 7. Comandos mínimos esperados

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api pytest tests/unit tests/integration -q