# Flujos Operativos — Back Office MLM Ganoherb

> **Documento tecnico.** Descripcion paso a paso de cada flujo funcional del MVP (Fase 1).
> Para la version de alto nivel dirigida a gerencia, ver `back_office_portal/plan.md` seccion 7.

---

## Tabla de Contenido

1. [Login de Usuario Administrativo](#1-login-de-usuario-administrativo)
2. [Inscripcion de Nuevo Distribuidor](#2-inscripcion-de-nuevo-distribuidor)
3. [Confirmacion de Pago de Orden](#3-confirmacion-de-pago-de-orden)
4. [Visualizacion de Genealogia (Arbol Binario)](#4-visualizacion-de-genealogia-arbol-binario)
5. [Listado y Busqueda de Distribuidores](#5-listado-y-busqueda-de-distribuidores)
6. [Catalogo de Productos y Kits](#6-catalogo-de-productos-y-kits)
7. [Detalle de Orden](#7-detalle-de-orden)
8. [Bono de Patrocinio Directo](#8-bono-de-patrocinio-directo)
9. [Cierre de Periodo y Calculo de Bono Binario](#9-cierre-de-periodo-y-calculo-de-bono-binario)
10. [Login de Distribuidor](#10-login-de-distribuidor)

---

## 1. Login de Usuario Administrativo

**Actor:** Administrador, Gerente de Ventas, Soporte.
**Endpoint:** `POST /api/v1/auth/login`

| Paso | Accion del usuario | Respuesta del sistema |
|------|--------------------|-----------------------|
| 1 | Accede al portal web. | Muestra pantalla de login (email + contrasena). |
| 2 | Ingresa credenciales y presiona "Iniciar sesion". | Valida email + password_hash (bcrypt) contra tabla `users`. |
| 3 | — | **Exito:** Genera JWT access token (15min) + refresh token (7 dias). Redirige al modulo principal. Resetea `failed_login_count`. Actualiza `last_login_at`. |
| 4 | — | **Error 401:** "Correo o contrasena incorrectos." Incrementa `failed_login_count`. |
| 5 | — | **Error 423:** Si `failed_login_count >= 5`, setea `locked_until = now() + 30min`. Muestra "Cuenta bloqueada temporalmente." |

**Tokens:**
- Access token en header `Authorization: Bearer <token>` para cada request.
- Refresh automatico: cuando el access token expira (401), el frontend usa el refresh token en `POST /api/v1/auth/refresh` para obtener nuevos tokens sin re-login.
- Si el refresh token tambien expiro (7 dias sin actividad), redirige a login.

**Auditoria:** Se registra cada login exitoso y fallido en `audit_logs` con IP y user_agent.

---

## 2. Inscripcion de Nuevo Distribuidor

**Actor:** Admin o Gerente de Ventas (permiso `affiliates:create`).
**Endpoints:** `GET /api/v1/products?kits_only=true`, `POST /api/v1/affiliates/enroll`
**Precondicion:** Usuario logueado con permisos.

### Paso 1 — Seleccion de kit

| Accion | Sistema |
|--------|---------|
| El admin navega a "Nuevo Distribuidor". | Fetch `GET /products?kits_only=true`. Muestra 3 cards: |
| | ESP1 = $195 (PV:100, BV:100) |
| | ESP2 = $495 (PV:300, BV:300) |
| | ESP3 = $995 (PV:600, BV:600) |
| Selecciona un kit. | Navega al formulario con el kit seleccionado. |

### Paso 2 — Formulario de inscripcion

**Campos del formulario:**

| Campo | Requerido | Validacion |
|-------|-----------|------------|
| Kit seleccionado | Si (readonly) | Viene del paso anterior. |
| Patrocinador (sponsor) | Opcional | Busqueda por codigo de distribuidor (`affiliate_code`). Debe existir y estar activo. |
| Posicion en arbol: padre de colocacion | Opcional | UUID del affiliate padre. Si sponsor tiene posiciones directas libres, se ofrece como default. |
| Posicion en arbol: pierna (izq/der) | Si, si hay padre | `left` o `right`. La posicion debe estar disponible. |
| Nombre | Si | min 1, max 100 chars. |
| Apellido | Si | min 1, max 100 chars. |
| Correo electronico | Si | Formato email valido. Unico en el sistema (tabla `users` y `affiliates`). |
| Telefono | Opcional | max 30 chars. |
| Tipo doc identidad | Condicional | DUI, Cedula, Pasaporte. Requerido si no se proporciona doc fiscal. |
| Numero doc identidad | Condicional | Requerido si se ingreso tipo doc identidad. |
| Tipo ID fiscal | Condicional | NIT, RFC, RUC. Requerido si no se proporciona doc identidad. |
| Numero ID fiscal | Condicional | Requerido si se ingreso tipo ID fiscal. |
| Contrasena | Si | Min 8 caracteres. Se hashea con bcrypt antes de guardar. |
| Direccion (line1, line2, ciudad, depto, CP) | Opcional | — |

**Validacion clave:** Al menos un par de documentos completo (identidad O fiscal).

### Paso 3 — Procesamiento (transaccion unica)

Al presionar "Inscribir Distribuidor", el backend ejecuta en **una sola transaccion**:

```
1. Validar unicidad de email (en users Y affiliates).
2. Validar sponsor existe y esta activo (si se proporciono).
3. Validar posicion en arbol disponible (si se proporciono).
4. Crear registro en `users`:
   - email, password_hash (bcrypt), first_name, last_name, is_active=true.
   - Asignar rol "distribuidor".
5. Crear registro en `affiliates`:
   - Vinculado al user (user_id FK).
   - sponsor_id, placement_parent_id, placement_side.
   - Generar affiliate_code: nextval('affiliate_seq_sv') → 'GH-SV-000001'.
   - kit_tier del kit seleccionado.
   - status = 'pending' (pendiente hasta confirmar pago).
6. Crear registro en `orders`:
   - order_type = 'enrollment', status = 'pending_payment'.
   - Generar order_number: 'ORD-YYYYMMDD-XXXX'.
   - Crear order_item con snapshot del precio, PV, BV del kit.
7. Registrar en audit_logs (action: 'affiliate.create').
```

### Paso 4 — Pantalla de confirmacion

Muestra:
- Codigo del distribuidor: `GH-SV-000001` (resaltado, copiable).
- Nombre completo y email.
- Kit adquirido con precio, PV y BV.
- Numero de orden y estado: "Pendiente de pago".
- Posicion en el arbol: "Pierna [izquierda/derecha] de [codigo del padre]".

### Paso 5 — Notificacion por email (SendGrid)

Se envian dos correos:

**a) Al nuevo distribuidor:**
- Asunto: "Bienvenido a Ganoherb — Tu codigo de distribuidor"
- Contenido: Codigo de distribuidor, credenciales de acceso (email + contrasena temporal o enlace), resumen del kit, datos de su patrocinador.

**b) Al administrador que lo inscribio:**
- Asunto: "Nuevo distribuidor inscrito — [codigo]"
- Contenido: Datos del distribuidor, kit, orden, posicion en el arbol.

**Implementacion:** SendGrid API con plantillas transaccionales. API key en variable de entorno `SENDGRID_API_KEY`. Envio asincrono (no bloquea la respuesta de la API).

### Errores posibles

| Error | Mensaje al usuario |
|-------|-------------------|
| Email duplicado | "Ya existe un distribuidor con este correo electronico." |
| Posicion ocupada | "La posicion seleccionada en el arbol ya esta ocupada." |
| Sponsor no encontrado | "El patrocinador no fue encontrado." |
| Sponsor inactivo | "El patrocinador no esta activo." |
| Sin documento | "Debe proporcionar al menos un documento de identificacion." |

---

## 3. Confirmacion de Pago de Orden

**Actor:** Admin o Gerente de Ventas (permiso `orders:update`).
**Endpoint:** `PATCH /api/v1/orders/{id}/confirm-payment` (por implementar).
**Precondicion:** Orden en estado `pending_payment`.

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | El admin busca la orden (por numero, codigo de distribuidor, o listado de pendientes). | Muestra detalle: productos, montos, estado actual. |
| 2 | Verifica que el pago fue recibido e ingresa metodo de pago y referencia. | Valida que la orden este en `pending_payment`. |
| 3 | Presiona "Confirmar Pago". | **Transaccion unica:** |
| | | a) `orders.status` → `paid`. Registra `paid_at`, `payment_method`, `payment_reference`. |
| | | b) Acredita PV al distribuidor: `affiliates.pv_current_period += order.total_pv`. |
| | | c) Acredita BV al upline: recorre el arbol binario hacia arriba desde el distribuidor. Para cada ancestro, suma `order.total_bv` a la pierna correspondiente (`bv_left_total` o `bv_right_total`). |
| | | d) Si es orden de inscripcion: `affiliates.status` → `active`. |
| | | e) Registra en `audit_logs`. |
| 4 | — | Muestra confirmacion: "Pago registrado. BV/PV acreditados. Distribuidor activado." |
| 5 | — | Envia email al distribuidor confirmando pago y activacion. |

**Regla critica (Regla #4):** Solo pedidos pagados generan BV/PV. Esta transicion es el unico punto donde se acredita volumen.

**Acreditacion de BV al upline — ejemplo:**
```
Arbol:        A
             / \
            B   C
           /
          D  ← nuevo distribuidor (compra kit ESP2, BV=300)

Al confirmar pago de D:
- D.pv_current_period += 300
- B.bv_left_total += 300   (D esta en la pierna izq de B)
- A.bv_left_total += 300   (B esta en la pierna izq de A)
```

---

## 4. Visualizacion de Genealogia (Arbol Binario)

**Actor:** Admin, Gerente de Ventas, Gerente de Operaciones (permiso `affiliates:read`).
**Endpoint:** `GET /api/v1/affiliates/{id}/tree` (por implementar).

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | Navega al modulo de genealogia. | Muestra arbol binario desde la raiz o desde un nodo seleccionado. |
| 2 | Navega por el arbol (expandir/colapsar, click en nodo). | Cada nodo muestra: codigo, nombre, rango (icono/color), estado, BV izq/der. |
| 3 | Busca distribuidor por codigo o nombre. | Resalta el nodo y muestra su camino hasta la raiz. |
| 4 | Ve posiciones vacias. | Icono "+" o nodo vacio indicando posicion disponible. |

**MVP:** Arbol con 3-4 niveles visibles. Lazy loading para profundidad mayor. Panel lateral con detalle al hacer click en un nodo.

**Endpoint propuesto:** Retorna nodos con `{affiliate_code, full_name, status, current_rank, bv_left_total, bv_right_total, left_child: {...} | null, right_child: {...} | null}`. Parametro `depth` para controlar niveles (default 3).

---

## 5. Listado y Busqueda de Distribuidores

**Actor:** Cualquier admin con permiso `affiliates:read`.
**Endpoint:** `GET /api/v1/affiliates`

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | Navega al listado de distribuidores. | Tabla paginada: codigo, nombre, email, rango, estado, fecha inscripcion. |
| 2 | Filtra por estado (activo, pendiente, inactivo, suspendido). | Query param `?status=active`. |
| 3 | Busca por nombre, email o codigo. | Filtrado server-side o client-side segun volumen. |
| 4 | Click en distribuidor. | Navega a detalle completo: datos personales, documentos, sponsor, posicion en arbol, BV/PV, ordenes. |

---

## 6. Catalogo de Productos y Kits

**Actor:** Cualquier admin con permiso `products:read`.
**Endpoint:** `GET /api/v1/products`

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | Navega al catalogo. | Lista/grid de productos activos: SKU, nombre, precio publico, precio distribuidor, PV, BV. |
| 2 | Filtra solo kits. | Query param `?kits_only=true`. Muestra ESP1, ESP2, ESP3. |
| 3 | Click en producto. | Detalle: descripcion, precios, volumenes, disponibilidad. |

---

## 7. Detalle de Orden

**Actor:** Cualquier admin con permiso `orders:read`.
**Endpoint:** `GET /api/v1/orders/{id}`

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | Accede al detalle (desde listado o perfil del distribuidor). | Muestra: numero de orden, tipo, estado, productos con cantidades/precios, PV/BV total, metodo de pago, distribuidor. |
| 2 | Si esta en `pending_payment`, muestra boton "Confirmar Pago" (→ Flujo 3). | |
| 3 | Si esta pagada, muestra referencia y fecha de pago. | |

---

## 8. Bono de Patrocinio Directo

**Actor:** Sistema (automatico).
**Trigger:** Confirmacion de pago de orden de inscripcion (Flujo 3).

| Paso | Sistema |
|------|---------|
| 1 | Al confirmar pago de orden de inscripcion, identifica al `sponsor_id` del distribuidor. |
| 2 | Verifica que el sponsor este activo (PV del periodo >= minimo). |
| 3 | Calcula bono: `order.total_bv x porcentaje_configurado` (default 20%). |
| 4 | Crea registro en tabla de comisiones: tipo `direct_sponsorship`, estado `pending_liquidation`, monto calculado. |
| 5 | El bono se incluye en la proxima liquidacion del periodo. |

**Nota:** En fase futura puede ser pago inmediato (acreditacion a billetera virtual).

---

## 9. Cierre de Periodo y Calculo de Bono Binario

**Actor:** Sistema + Gerente de Operaciones (aprobacion).
**Frecuencia:** Semanal o quincenal (configurable).

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | Admin o cron inicia cierre de periodo. | Congela snapshot de BV por pierna para cada distribuidor activo. |
| 2 | — | Para cada distribuidor calificado (PV >= minimo, al menos 1 activo por pierna): |
| | | a) Pierna debil = `min(bv_left_total, bv_right_total)`. |
| | | b) Bono = `pierna_debil x porcentaje_segun_rango` (10%-15%). |
| | | c) Descuenta BV pareado de ambas piernas. |
| | | d) Carry-over = excedente de pierna fuerte (hasta tope = 3x tope semanal). |
| | | e) Flush del excedente si supera el carry-over maximo. |
| | | f) Aplica tope de ganancias segun rango. |
| 3 | — | Genera reporte de pre-liquidacion. |
| 4 | Gerente revisa y aprueba. | Registra comisiones como aprobadas. Cierra el periodo (inmutable, Regla #12). |

---

## 10. Login de Distribuidor

**Actor:** Distribuidor/Afiliado.
**Endpoint:** `POST /api/v1/auth/login` (mismo endpoint, diferente rol).
**Precondicion:** Distribuidor fue inscrito (Flujo 2) y su pago fue confirmado (Flujo 3, status `active`).

| Paso | Accion | Sistema |
|------|--------|---------|
| 1 | Accede al portal. | Pantalla de login. |
| 2 | Ingresa email y contrasena (creados en Flujo 2). | Valida credenciales. |
| 3 | — | Redirige a oficina virtual del distribuidor (vista de solo lectura en MVP). |
| 4 | Puede ver: | |
| | - Codigo y datos personales. | |
| | - Posicion en arbol binario (upline y downline). | |
| | - Acumuladores: PV del periodo, BV pierna izq/der. | |
| | - Ordenes asociadas. | |
| | - Comisiones y bonos (cuando se implementen). | |

**Nota MVP:** La oficina virtual es solo lectura. Acciones (compras, autoship, editar perfil) se implementan en fases posteriores.

---

## Resumen: Estado por Flujo

| # | Flujo | Sub-fase | Backend | Frontend |
|---|-------|----------|---------|----------|
| 1 | Login admin | 1.1 | Hecho | Pendiente |
| 2 | Inscripcion distribuidor | 1.2 | Parcial (falta crear User + contrasena + email SendGrid) | Pendiente |
| 3 | Confirmacion de pago | 1.4 | Pendiente | Pendiente |
| 4 | Genealogia (arbol) | 1.3 | Pendiente | Pendiente |
| 5 | Listado distribuidores | 1.2 | Hecho | Pendiente |
| 6 | Catalogo productos | 1.2 | Hecho | Pendiente |
| 7 | Detalle de orden | 1.2 | Hecho | Pendiente |
| 8 | Bono patrocinio | 1.5 | Pendiente | N/A (automatico) |
| 9 | Cierre periodo / binario | Fase 2 | Pendiente | Pendiente |
| 10 | Login distribuidor | 1.2 | Parcial (falta rol distribuidor + User en enrollment) | Pendiente |
