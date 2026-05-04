# Matriz de permisos

Este documento define los criterios de acceso para los endpoints actuales de la API y establece reglas para módulos futuros.

La matriz sirve como referencia antes de agregar o modificar endpoints. El objetivo es evitar permisos ambiguos, endpoints administrativos expuestos por error o reglas inconsistentes entre módulos.

## 1. Niveles de acceso

La API distingue los siguientes niveles de acceso:

| Nivel | Descripción |
|---|---|
| Público | No requiere access token. |
| Usuario autenticado | Requiere access token válido. |
| Dueño del recurso | Usuario autenticado que opera sobre sus propios datos. |
| Superusuario | Usuario con permisos administrativos. |
| Token específico | No requiere access token, pero requiere un token funcional válido, por ejemplo refresh token o reset token. |

## 2. Reglas generales

Antes de agregar un endpoint nuevo, debe definirse:

- si es público o protegido;
- si requiere usuario autenticado;
- si requiere que el usuario sea dueño del recurso;
- si requiere superusuario;
- si genera evento de auditoría;
- si debe tener rate limiting;
- si expone datos sensibles;
- si modifica estado persistente.

Regla base:

```text
Todo endpoint que modifique usuarios, sesiones, recuperación de contraseña, auditoría, catálogo administrativo o estado persistente sensible debe estar protegido o condicionado por un token específico válido.
```

## 3. Auth

| Endpoint | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `POST /api/v1/auth/register` | Público | Sí | Registro público. Debe impedir autoelevación de privilegios. |
| `POST /api/v1/auth/login` | Público | Sí | Debe tener rate limiting. |
| `POST /api/v1/auth/refresh-token` | Token específico | Sí | Requiere refresh token válido, vigente y no revocado. |
| `POST /api/v1/auth/logout` | Token específico | Sí | Revoca el refresh token enviado. |
| `POST /api/v1/auth/logout-all` | Usuario autenticado | Sí | Revoca todas las sesiones del usuario autenticado. |
| `POST /api/v1/auth/forgot-password` | Público | Sí | Debe responder de forma neutra para evitar enumeración de correos. |
| `POST /api/v1/auth/reset-password` | Token específico | Sí | Requiere token de recuperación válido, no usado y no expirado. |
| `GET /api/v1/auth/me` | Usuario autenticado | No obligatorio | Devuelve el usuario autenticado actual. |

## 4. Users

| Endpoint | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `GET /api/v1/users` | Superusuario | No obligatorio | Listado administrativo. |
| `GET /api/v1/users/{user_id}` | Dueño del recurso o superusuario | No obligatorio | Un usuario normal solo debe consultar su propio perfil. |
| `POST /api/v1/users` | Superusuario | Sí | Creación administrativa de usuarios. |
| `PUT /api/v1/users/{user_id}` | Dueño del recurso o superusuario | Sí | Usuario normal no debe modificar campos privilegiados. |
| `PATCH /api/v1/users/{user_id}` | Dueño del recurso o superusuario | Sí | Usuario normal no debe modificar campos privilegiados. |
| `POST /api/v1/users/{user_id}/change-password` | Dueño del recurso o superusuario | Sí | Debe validar contraseña actual cuando aplica. |
| `PATCH /api/v1/users/{user_id}/activate` | Superusuario | Sí | Acción administrativa. |
| `PATCH /api/v1/users/{user_id}/deactivate` | Superusuario | Sí | Acción administrativa. |
| `DELETE /api/v1/users/{user_id}` | Superusuario | Sí | Eliminación lógica o física según implementación. |
| `PATCH /api/v1/users/{user_id}/restore` | Superusuario | Sí | Restauración administrativa. |

## 5. Products

| Endpoint | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `GET /api/v1/products` | Público | No obligatorio | Catálogo público. No debe exponer productos eliminados lógicamente. |
| `GET /api/v1/products/{id}` | Público | No obligatorio | Consulta pública de producto activo/no eliminado. |
| `POST /api/v1/products` | Usuario autenticado | Sí | En la implementación actual requiere usuario autenticado. Puede endurecerse a superusuario en un PR posterior. |
| `PUT /api/v1/products/{id}` | Usuario autenticado | Sí | En la implementación actual requiere usuario autenticado. Puede endurecerse a superusuario en un PR posterior. |
| `PATCH /api/v1/products/{id}` | Usuario autenticado | Sí | En la implementación actual requiere usuario autenticado. Puede endurecerse a superusuario en un PR posterior. |
| `PATCH /api/v1/products/{id}/activate` | Superusuario | Sí | Acción administrativa. |
| `PATCH /api/v1/products/{id}/deactivate` | Superusuario | Sí | Acción administrativa. |
| `DELETE /api/v1/products/{id}` | Superusuario | Sí | Acción administrativa. |
| `PATCH /api/v1/products/{id}/restore` | Superusuario | Sí | Acción administrativa. |

## 6. Categories

| Endpoint | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `GET /api/v1/categories` | Público | No obligatorio | Devuelve categorías activas y no eliminadas. |
| `GET /api/v1/categories/{category_id}` | Público | No obligatorio | Devuelve una categoría activa y no eliminada. |
| `POST /api/v1/categories` | Superusuario | Sí | Creación administrativa de categorías. |
| `PUT /api/v1/categories/{category_id}` | Superusuario | Sí | Actualización completa de categoría. |
| `PATCH /api/v1/categories/{category_id}` | Superusuario | Sí | Actualización parcial de categoría. |
| `PATCH /api/v1/categories/{category_id}/activate` | Superusuario | Sí | Acción administrativa. |
| `PATCH /api/v1/categories/{category_id}/deactivate` | Superusuario | Sí | Acción administrativa. |
| `DELETE /api/v1/categories/{category_id}` | Superusuario | Sí | Eliminación lógica. |
| `PATCH /api/v1/categories/{category_id}/restore` | Superusuario | Sí | Restauración administrativa. |

Las categorías funcionan como catálogo administrativo. La lectura es pública, pero toda operación de escritura requiere superusuario.

La consulta pública debe devolver únicamente categorías con:

```text
is_active = True
is_deleted = False
```

## 7. Audit Logs

| Endpoint | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `GET /api/v1/audit-logs` | Superusuario | No obligatorio | Solo debe estar disponible para superusuario. |

Los logs de auditoría pueden contener trazabilidad operativa. No deben exponerse a usuarios normales.

## 8. Módulos futuros

Los siguientes módulos aún no forman parte de la API principal, pero la matriz define el criterio esperado para cuando se implementen.

## 9. Inventory

| Endpoint futuro | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `GET /api/v1/inventory` | Superusuario | No obligatorio | Consulta administrativa. |
| `GET /api/v1/inventory/{product_id}` | Superusuario | No obligatorio | Consulta administrativa por producto. |
| `PATCH /api/v1/inventory/{product_id}` | Superusuario | Sí | Ajuste manual de stock. |
| `POST /api/v1/inventory/{product_id}/reserve` | Usuario autenticado o flujo interno | Sí | Debe usarse dentro de flujos transaccionales. |
| `POST /api/v1/inventory/{product_id}/release` | Usuario autenticado o flujo interno | Sí | Debe liberar stock reservado cuando se cancele una orden. |

El inventario debe tratarse como dato crítico. Debe cuidarse la consistencia ante órdenes, cancelaciones y pagos.

## 10. Cart

| Endpoint futuro | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `GET /api/v1/cart` | Usuario autenticado | No obligatorio | Usuario consulta su propio carrito. |
| `POST /api/v1/cart/items` | Usuario autenticado | No obligatorio | Agrega producto al carrito del usuario autenticado. |
| `PATCH /api/v1/cart/items/{item_id}` | Dueño del recurso | No obligatorio | Modifica cantidad de un item propio. |
| `DELETE /api/v1/cart/items/{item_id}` | Dueño del recurso | No obligatorio | Elimina item propio. |
| `DELETE /api/v1/cart` | Usuario autenticado | No obligatorio | Vacía carrito propio. |

Un usuario no debe poder consultar ni modificar carritos de otros usuarios.

## 11. Orders

| Endpoint futuro | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `POST /api/v1/orders` | Usuario autenticado | Sí | Crea orden desde carrito o payload válido. |
| `GET /api/v1/orders` | Usuario autenticado o superusuario | No obligatorio | Usuario ve sus órdenes; superusuario puede listar todas. |
| `GET /api/v1/orders/{order_id}` | Dueño del recurso o superusuario | No obligatorio | Usuario solo ve sus propias órdenes. |
| `PATCH /api/v1/orders/{order_id}/cancel` | Dueño del recurso o superusuario | Sí | Usuario puede cancelar si el estado lo permite. |
| `PATCH /api/v1/orders/{order_id}/status` | Superusuario | Sí | Cambio administrativo de estado. |

Las órdenes requieren reglas de transición de estado. No debe permitirse cualquier cambio arbitrario.

## 12. Payments

| Endpoint futuro | Acceso requerido | Auditoría | Observaciones |
|---|---|---:|---|
| `POST /api/v1/payments/simulate` | Usuario autenticado | Sí | Pago simulado para pruebas de flujo. |
| `GET /api/v1/payments/{payment_id}` | Dueño del recurso o superusuario | No obligatorio | Usuario consulta pagos propios. |
| `PATCH /api/v1/payments/{payment_id}/refund` | Superusuario | Sí | Reembolso administrativo. |

Aunque el pago sea simulado, debe tratarse como flujo sensible.

## 13. Regla para dueño del recurso

Cuando un endpoint permita acceso por dueño del recurso, el backend debe validar la relación real en base de datos.

No basta con confiar en IDs enviados por el cliente.

Ejemplo:

```text
Correcto:
- leer usuario autenticado desde token
- consultar orden en base de datos
- verificar que order.user_id == current_user.id

Incorrecto:
- aceptar user_id del body
- confiar en que el cliente envió su propio ID
```

## 14. Regla para superusuario

El superusuario puede ejecutar acciones administrativas, pero debe mantenerse la auditoría.

Toda acción administrativa que modifique estado relevante debe registrar:

- acción;
- entidad;
- ID de entidad si aplica;
- actor;
- rol;
- request_id;
- estado;
- detalle;
- fecha.

## 15. Rate limiting por permisos

Los endpoints públicos y sensibles deben tener prioridad para rate limiting.

Ejemplos:

| Endpoint | Rate limiting recomendado |
|---|---:|
| `POST /api/v1/auth/login` | Sí |
| `POST /api/v1/auth/register` | Sí |
| `POST /api/v1/auth/forgot-password` | Sí |
| `POST /api/v1/auth/reset-password` | Sí |
| `POST /api/v1/payments/simulate` | Sí |
| Endpoints administrativos internos | Según exposición |

## 16. Checklist de permisos para nuevos endpoints

Antes de abrir un Pull Request con endpoints nuevos, responder:

```text
¿El endpoint es público?
¿Requiere access token?
¿Requiere superusuario?
¿El usuario solo puede operar sobre su propio recurso?
¿El recurso pertenece realmente al usuario autenticado?
¿Debe auditarse?
¿Debe tener rate limiting?
¿Expone datos sensibles?
¿Puede modificar estado crítico?
¿Tiene pruebas de acceso permitido y acceso denegado?
```

## 17. Pruebas mínimas de permisos

Cada endpoint protegido debe incluir pruebas para:

- acceso sin token;
- acceso con token inválido si aplica;
- acceso con usuario normal;
- acceso con superusuario;
- acceso a recurso propio;
- intento de acceso a recurso de otro usuario;
- operación exitosa;
- operación denegada.

No todos los casos aplican a todos los endpoints, pero la decisión debe ser explícita.

## 18. Criterio antes de merge

Antes de fusionar cambios que agreguen endpoints:

```text
La matriz de permisos debe estar actualizada.
Las pruebas de autorización deben pasar.
Los eventos auditables deben estar cubiertos.
No debe haber endpoints administrativos expuestos como públicos por accidente.
```