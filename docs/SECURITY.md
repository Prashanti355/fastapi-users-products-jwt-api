# Seguridad

Este documento resume los mecanismos de seguridad implementados en la API y las reglas que deben mantenerse al expandir el proyecto.

## 1. Visión general

La API incluye mecanismos de seguridad para autenticación, autorización, control de sesiones, recuperación de contraseña, protección contra abuso y auditoría.

Los componentes principales son:

- JWT;
- access tokens;
- refresh tokens persistidos;
- rotación de refresh tokens;
- logout individual;
- logout global;
- recuperación de contraseña;
- roles;
- rate limiting;
- auditoría;
- CORS;
- manejo controlado de errores;
- separación de secretos mediante variables de entorno.

## 2. Autenticación

La autenticación se realiza mediante JWT.

El flujo general es:

```text
usuario envía credenciales
  ↓
la API valida usuario y contraseña
  ↓
la API genera access token
  ↓
la API genera refresh token
  ↓
el cliente usa el access token para endpoints protegidos
```

El access token tiene una vida corta. El refresh token permite renovar sesión sin volver a enviar credenciales.

## 3. Access token

El access token se usa para autenticar peticiones protegidas.

Debe enviarse en el header:

```http
Authorization: Bearer <access_token>
```

El token contiene información mínima para identificar al usuario y su rol.

No debe almacenarse información sensible dentro del JWT.

## 4. Refresh token

Los refresh tokens se almacenan en PostgreSQL y tienen un identificador único (`jti`).

La API permite:

- persistir refresh tokens;
- validar refresh tokens activos;
- rotar refresh tokens;
- revocar refresh tokens;
- cerrar sesión individual;
- cerrar todas las sesiones de un usuario;
- invalidar sesiones después de restablecer contraseña;
- limpiar tokens expirados o revocados antiguos.

## 5. Rotación de refresh tokens

Cuando se usa un refresh token para renovar sesión, la API puede emitir un nuevo refresh token y revocar el anterior.

Esto reduce el riesgo de reutilización de tokens comprometidos.

El flujo esperado es:

```text
cliente envía refresh token
  ↓
API valida que exista, no esté revocado y no esté expirado
  ↓
API revoca el refresh token anterior
  ↓
API emite nuevos tokens
```

## 6. Logout individual

El endpoint de logout revoca el refresh token enviado.

Resultado esperado:

```text
el refresh token queda inválido
el usuario no puede usarlo para renovar sesión
```

## 7. Logout global

El endpoint de logout global revoca todas las sesiones activas del usuario autenticado.

Esto es útil cuando:

- el usuario sospecha que su cuenta fue comprometida;
- se cambia contraseña;
- se quiere cerrar sesión en todos los dispositivos.

## 8. Recuperación de contraseña

La recuperación de contraseña usa tokens persistidos en PostgreSQL.

El flujo general es:

```text
usuario solicita recuperación
  ↓
API genera token de recuperación
  ↓
API envía correo mediante Resend
  ↓
usuario usa el token para restablecer contraseña
  ↓
API marca el token como usado
  ↓
API revoca refresh tokens activos del usuario
```

Cada token debe cumplir:

- existir en base de datos;
- pertenecer al usuario correcto;
- no estar expirado;
- no haber sido usado previamente.

La respuesta del endpoint de solicitud debe ser neutra para evitar enumeración de correos.

## 9. Roles y autorización

El sistema distingue entre:

```text
público
usuario autenticado
superusuario
```

Ejemplos de acceso:

| Recurso | Público | Usuario autenticado | Superusuario |
|---|---:|---:|---:|
| Registro | Sí | Sí | Sí |
| Login | Sí | Sí | Sí |
| Consultar productos públicos | Sí | Sí | Sí |
| Crear productos | Según regla del endpoint | Según regla del endpoint | Sí |
| Activar/desactivar productos | No | No | Sí |
| Listar usuarios | No | No | Sí |
| Consultar mi usuario | No | Sí | Sí |
| Audit logs | No | No | Sí |

Cuando se agreguen nuevos módulos, debe definirse una matriz de permisos antes de escribir endpoints.

## 10. Rate limiting

La API usa rate limiting para proteger endpoints sensibles.

Actualmente se contempla protección para:

- login;
- registro;
- otros endpoints sensibles si se decide extenderlo.

La configuración se controla mediante variables de entorno:

```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_STORAGE_URI="memory://"
RATE_LIMIT_HEADERS_ENABLED=True
RATE_LIMIT_LOGIN="200/minute"
RATE_LIMIT_REGISTER="100/minute"
```

En CI/testing pueden usarse límites más bajos para probar respuestas `429 Too Many Requests` de forma estable.

## 11. Auditoría

La API registra eventos sensibles en la tabla `audit_logs`.

Ejemplos de eventos auditables:

- `register`;
- `login`;
- `refresh_token`;
- `logout`;
- `logout_all`;
- `forgot_password`;
- `reset_password`;
- `create_user`;
- `update_user`;
- `change_password`;
- `activate_user`;
- `deactivate_user`;
- `delete_user`;
- `restore_user`;
- `create_product`;
- `update_product`;
- `activate_product`;
- `deactivate_product`;
- `delete_product`;
- `restore_product`.

Cada evento debe conservar información suficiente para trazabilidad, sin exponer secretos.

## 12. Request ID

Cada petición recibe un `request_id`.

Este valor permite correlacionar:

- logs técnicos;
- respuestas HTTP;
- eventos de auditoría.

Cuando se investigue un error, el `request_id` debe servir como punto de unión entre la petición y los registros internos.

## 13. CORS

CORS se configura mediante `BACKEND_CORS_ORIGINS`.

En desarrollo puede incluir:

```env
BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
```

En producción debe limitarse a los dominios reales del frontend o clientes autorizados.

No debe usarse una configuración abierta sin necesidad.

## 14. Secretos y variables de entorno

No deben versionarse:

- `.env`;
- claves de Resend;
- `SECRET_KEY` real;
- credenciales reales de base de datos;
- tokens;
- archivos de logs con información sensible.

El archivo `.env.example` debe contener solo valores de ejemplo.

Si una clave se expone accidentalmente, debe rotarse antes de continuar el desarrollo o desplegar cambios.

## 15. Revisión de secretos antes de commit

Antes de subir cambios, ejecutar:

```bash
git status
git grep "RESEND_API_KEY"
git grep "SECRET_KEY"
git grep "re_"
```

`git grep "re_"` puede devolver coincidencias normales como `refresh_token` o `restore_user`. Lo importante es que no aparezcan claves reales con formato similar a una API key.

## 16. Reglas para nuevos módulos

Cuando se agregue un nuevo módulo, debe revisarse:

- qué endpoints serán públicos;
- qué endpoints requieren usuario autenticado;
- qué endpoints requieren superusuario;
- qué eventos deben auditarse;
- qué acciones requieren rate limiting;
- qué datos no deben exponerse en responses;
- qué errores deben manejarse de forma neutra;
- si se requieren transacciones para mantener consistencia.

## 17. Criterio mínimo de seguridad antes de merge

Antes de fusionar un PR, debe verificarse:

```text
no hay .env versionado
no hay claves reales
no hay credenciales reales
los endpoints protegidos requieren autorización
las operaciones administrativas requieren superusuario
las pruebas relevantes pasan
```

La seguridad debe revisarse como parte del diseño de cada módulo, no como un parche posterior.