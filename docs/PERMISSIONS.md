# Matriz de permisos

Este documento define los criterios de acceso para los endpoints actuales de la API y establece la regla que deben seguir los módulos futuros.

La matriz sirve como referencia antes de agregar nuevos módulos de negocio. El objetivo es evitar permisos ambiguos, endpoints administrativos expuestos por error o reglas inconsistentes entre módulos.

## 1. Roles considerados

La API distingue los siguientes niveles de acceso:

| Nivel | Descripción |
|---|---|
| Público | No requiere autenticación. |
| Usuario autenticado | Requiere access token válido. |
| Dueño del recurso | Usuario autenticado que opera sobre sus propios datos. |
| Superusuario | Usuario con permisos administrativos. |

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
Todo endpoint que modifique datos sensibles, usuarios, permisos, sesiones, productos administrativos o auditoría debe estar protegido.
```

## 3. Auth

| Endpoint | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `POST /api/v1/auth/register` | Sí | Sí | No aplica | Sí | Sí | Registro público. Debe impedir autoelevación de privilegios. |
| `POST /api/v1/auth/login` | Sí | Sí | No aplica | Sí | Sí | Debe tener rate limiting. |
| `POST /api/v1/auth/refresh-token` | Sí | Sí | No aplica | Sí | Sí | Requiere refresh token válido. |
| `POST /api/v1/auth/logout` | No | Sí | Sí | Sí | Sí | Revoca el refresh token enviado. |
| `POST /api/v1/auth/logout-all` | No | Sí | Sí | Sí | Sí | Revoca todas las sesiones del usuario autenticado. |
| `POST /api/v1/auth/forgot-password` | Sí | Sí | No aplica | Sí | Sí | Respuesta neutra para evitar enumeración de correos. |
| `POST /api/v1/auth/reset-password` | Sí | Sí | No aplica | Sí | Sí | Requiere token válido, no usado y no expirado. |
| `GET /api/v1/auth/me` | No | Sí | Sí | Sí | No obligatorio | Devuelve el usuario autenticado actual. |

## 4. Users

| Endpoint | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `GET /api/v1/users` | No | No | No | Sí | No obligatorio | Listado administrativo. |
| `GET /api/v1/users/{user_id}` | No | Sí | Sí | Sí | No obligatorio | Un usuario solo debe consultar su propio perfil, salvo superusuario. |
| `POST /api/v1/users` | No | No | No | Sí | Sí | Creación administrativa de usuarios. |
| `PUT /api/v1/users/{user_id}` | No | Sí | Sí | Sí | Sí | Usuario normal no debe modificar campos privilegiados. |
| `PATCH /api/v1/users/{user_id}` | No | Sí | Sí | Sí | Sí | Usuario normal no debe modificar campos privilegiados. |
| `POST /api/v1/users/{user_id}/change-password` | No | Sí | Sí | Sí | Sí | Debe validar contraseña actual. |
| `PATCH /api/v1/users/{user_id}/activate` | No | No | No | Sí | Sí | Acción administrativa. |
| `PATCH /api/v1/users/{user_id}/deactivate` | No | No | No | Sí | Sí | Acción administrativa. |
| `DELETE /api/v1/users/{user_id}` | No | No | No | Sí | Sí | Eliminación lógica o física según implementación. |
| `PATCH /api/v1/users/{user_id}/restore` | No | No | No | Sí | Sí | Restauración administrativa. |

## 5. Products

| Endpoint | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `GET /api/v1/products` | Sí | Sí | No aplica | Sí | No obligatorio | Catálogo público. No debe exponer productos eliminados lógicamente. |
| `GET /api/v1/products/{id}` | Sí | Sí | No aplica | Sí | No obligatorio | Consulta pública de producto activo/no eliminado. |
| `POST /api/v1/products` | No | Sí | No aplica | Según regla actual | Sí | Si se mantiene como operación administrativa, debe requerir superusuario. |
| `PUT /api/v1/products/{id}` | No | Sí | No aplica | Según regla actual | Sí | Debe proteger modificación de catálogo. |
| `PATCH /api/v1/products/{id}` | No | Sí | No aplica | Según regla actual | Sí | Debe proteger modificación parcial de catálogo. |
| `PATCH /api/v1/products/{id}/activate` | No | No | No aplica | Sí | Sí | Acción administrativa. |
| `PATCH /api/v1/products/{id}/deactivate` | No | No | No aplica | Sí | Sí | Acción administrativa. |
| `DELETE /api/v1/products/{id}` | No | No | No aplica | Sí | Sí | Acción administrativa. |
| `PATCH /api/v1/products/{id}/restore` | No | No | No aplica | Sí | Sí | Acción administrativa. |

## 6. Audit Logs

| Endpoint | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `GET /api/v1/audit-logs` | No | No | No | Sí | No obligatorio | Solo debe estar disponible para superusuario. |

Los logs de auditoría pueden contener trazabilidad operativa. No deben exponerse a usuarios normales.

## 7. Módulos futuros

Los siguientes módulos aún no forman parte de la API principal, pero la matriz define el criterio esperado para cuando se implementen.

## 8. Categories

| Endpoint futuro | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `GET /api/v1/categories` | Sí | Sí | No aplica | Sí | No obligatorio | Listado público de categorías activas. |
| `GET /api/v1/categories/{category_id}` | Sí | Sí | No aplica | Sí | No obligatorio | Consulta pública de categoría activa. |
| `POST /api/v1/categories` | No | No | No aplica | Sí | Sí | Creación administrativa. |
| `PATCH /api/v1/categories/{category_id}` | No | No | No aplica | Sí | Sí | Actualización administrativa. |
| `PATCH /api/v1/categories/{category_id}/activate` | No | No | No aplica | Sí | Sí | Acción administrativa. |
| `PATCH /api/v1/categories/{category_id}/deactivate` | No | No | No aplica | Sí | Sí | Acción administrativa. |
| `DELETE /api/v1/categories/{category_id}` | No | No | No aplica | Sí | Sí | Eliminación administrativa. |

## 9. Inventory

| Endpoint futuro | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `GET /api/v1/inventory` | No | No | No aplica | Sí | No obligatorio | Consulta administrativa. |
| `GET /api/v1/inventory/{product_id}` | No | No | No aplica | Sí | No obligatorio | Consulta administrativa por producto. |
| `PATCH /api/v1/inventory/{product_id}` | No | No | No aplica | Sí | Sí | Ajuste manual de stock. |
| `POST /api/v1/inventory/{product_id}/reserve` | No | Sí | Según operación | Sí | Sí | Debe usarse dentro de flujos transaccionales. |
| `POST /api/v1/inventory/{product_id}/release` | No | Sí | Según operación | Sí | Sí | Debe liberar stock reservado cuando se cancele una orden. |

El inventario debe tratarse como dato crítico. Debe cuidarse la consistencia ante órdenes, cancelaciones y pagos.

## 10. Cart

| Endpoint futuro | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `GET /api/v1/cart` | No | Sí | Sí | Sí | No obligatorio | Usuario consulta su propio carrito. |
| `POST /api/v1/cart/items` | No | Sí | Sí | Sí | No obligatorio | Agrega producto al carrito del usuario autenticado. |
| `PATCH /api/v1/cart/items/{item_id}` | No | Sí | Sí | Sí | No obligatorio | Modifica cantidad de un item propio. |
| `DELETE /api/v1/cart/items/{item_id}` | No | Sí | Sí | Sí | No obligatorio | Elimina item propio. |
| `DELETE /api/v1/cart` | No | Sí | Sí | Sí | No obligatorio | Vacía carrito propio. |

Un usuario no debe poder consultar ni modificar carritos de otros usuarios.

## 11. Orders

| Endpoint futuro | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `POST /api/v1/orders` | No | Sí | Sí | Sí | Sí | Crea orden desde carrito o payload válido. |
| `GET /api/v1/orders` | No | Sí | Sí | Sí | No obligatorio | Usuario ve sus órdenes; superusuario puede listar todas. |
| `GET /api/v1/orders/{order_id}` | No | Sí | Sí | Sí | No obligatorio | Usuario solo ve sus propias órdenes. |
| `PATCH /api/v1/orders/{order_id}/cancel` | No | Sí | Sí | Sí | Sí | Usuario puede cancelar si el estado lo permite. |
| `PATCH /api/v1/orders/{order_id}/status` | No | No | No | Sí | Sí | Cambio administrativo de estado. |

Las órdenes requieren reglas de transición de estado. No debe permitirse cualquier cambio arbitrario.

## 12. Payments

| Endpoint futuro | Público | Usuario autenticado | Dueño del recurso | Superusuario | Auditoría | Observaciones |
|---|---:|---:|---:|---:|---:|---|
| `POST /api/v1/payments/simulate` | No | Sí | Sí | Sí | Sí | Pago simulado para pruebas de flujo. |
| `GET /api/v1/payments/{payment_id}` | No | Sí | Sí | Sí | No obligatorio | Usuario consulta pagos propios. |
| `PATCH /api/v1/payments/{payment_id}/refund` | No | No | No | Sí | Sí | Reembolso administrativo. |

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
¿Requiere token?
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
No debe haber endpoints administrativos expuestos como públicos.
```