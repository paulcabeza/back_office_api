# Ganoherb Back Office — Contexto Tecnico y Bitacora de Progreso

> **Empresa:** Ganoherb
> **Pais inicial:** El Salvador (expansion futura a otros paises)

## Estructura del Proyecto

- `back_office_api/` — Backend (FastAPI + Python) — **repo privado**
- `back_office_portal/` — Frontend (React + TypeScript) — **repo publico**
- `back_office_portal/plan.md` — Reglas de negocio core (compensacion, rangos, red binaria) — publico para revision del gerente
- `back_office_api/modulos.md` — Detalle funcional de cada modulo del sistema
- `back_office_api/context.md` — Contexto tecnico y bitacora (este archivo)

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|-----------|
| **Backend API** | Python + FastAPI |
| **Base de Datos** | PostgreSQL 17 (Neon — managed, instancias separadas dev/prod) |
| **ORM** | SQLAlchemy 2.0 async + Alembic (migraciones) |
| **Cache** | Redis 7 (Docker Compose local) |
| **Cola de Tareas** | Celery + Redis (calculos de comisiones asincrono) |
| **Frontend** | React + TypeScript |
| **Estado Frontend** | Zustand o Redux Toolkit |
| **UI Components** | Shadcn/ui + Tailwind CSS |
| **Autenticacion** | JWT (access + refresh tokens) |
| **Dependencias Python** | pip + venv (requirements.txt) |
| **Almacenamiento** | AWS S3 / MinIO |
| **Email** | SendGrid / AWS SES |
| **Despliegue** | Docker + Docker Compose (dev), AWS/GCP (prod) |
| **CI/CD** | GitHub Actions |
| **Monitoreo** | Sentry (errores), Prometheus + Grafana (metricas) |

---

## Arquitectura y Decisiones Tecnicas

### Seguridad y Auditoria

- Autenticacion JWT con refresh tokens.
- Roles y permisos granulares (RBAC).
- 2FA obligatorio para administradores, opcional para afiliados.
- Politica de contrasenas configurable (longitud, complejidad, expiracion).
- Bloqueo de cuenta tras intentos fallidos.
- Sesiones concurrentes controladas.
- Log de auditoria completo e inmutable (append-only): usuario, fecha/hora, IP, accion, datos anteriores y nuevos.
- Encriptacion de datos sensibles en reposo (datos bancarios, documentos).
- Comunicacion exclusiva por HTTPS.
- Cumplimiento GDPR / Ley de proteccion de datos local.
- Retencion de logs minimo 5 anos para cumplimiento fiscal.

### Validaciones de Negocio (App-level)

- **Documentos de afiliado:** Cada afiliado tiene dos pares de documentos: identidad personal (`id_doc_type`/`id_doc_number` — DUI, Cedula, INE, Passport) e identificacion fiscal (`tax_id_type`/`tax_id_number` — NIT, RFC, RUC, RUT). Ambos son nullable en BD, pero el servicio valida que **al menos uno sea proporcionado** al crear o activar un afiliado. Esto soporta el flujo donde un distribuidor inicia con un solo documento y completa el otro despues.

### Known Issues / Gotchas (Desarrollo)

- **asyncpg + Neon SSL:** asyncpg NO acepta `sslmode` ni `channel_binding` en query string de la URL. Se deben limpiar los parametros (`url.split("?")[0]`) y pasar SSL via `connect_args={"ssl": ssl.create_default_context()}`. Aplicado en `app/db/session.py` y `alembic/env.py`.
- **passlib + bcrypt:** passlib 1.7.4 es incompatible con bcrypt>=4.1. Se fijo `bcrypt==4.0.1` en requirements.txt.
- **user_roles con 2 FKs a users:** La tabla `user_roles` tiene `user_id` y `assigned_by` (ambos FK a users). Las relaciones en SQLAlchemy requieren `primaryjoin`/`secondaryjoin` explicitos.
- **Lazy load en async:** Cuando se crean objetos en memoria (no via query), las relaciones lazy no se cargan automaticamente. Usar `await db.refresh(obj, ["relationship"])` antes de serializar con Pydantic.
- **Git:** Identidad configurada per-repo (no global). SSH auth con ed25519. Remote: `git@github.com:paulcabeza/back_office_api.git`.
- **venv:** En `.venv/` dentro de `back_office_api/`. Python 3.12.

### Multi-Tenant (Fase Futura)

**Objetivo:** Convertir el sistema en una plataforma SaaS donde multiples empresas MLM puedan tener su propia instancia aislada.

**Estrategia de aislamiento:**

| Opcion | Descripcion | Pros | Contras |
|--------|-------------|------|---------|
| Schema por tenant | Cada tenant tiene su propio schema en la misma BD. | Buen balance costo/aislamiento. | Migraciones mas complejas. |
| BD por tenant | Base de datos separada por tenant. | Maximo aislamiento. | Mayor costo de infraestructura. |
| Row-level (tenant_id) | Todos comparten tablas, filtrados por tenant_id. | Menor costo, simple. | Riesgo de filtrar datos entre tenants. |

**Recomendacion:** Disenar desde el inicio con `tenant_id` en las tablas para facilitar la transicion futura. Schema por tenant como punto medio cuando se implemente.

**Personalizacion por tenant:** Branding, plan de compensacion independiente, catalogo propio, configuracion fiscal por pais, usuarios administrativos propios.

### Integraciones Externas

| Integracion | Proposito | Prioridad |
|-------------|-----------|-----------|
| Pasarela de pago (Stripe/PayU/Wompi) | Cobro de pedidos. | Alta |
| Facturacion electronica (Alegra/Siigo) | Emision de facturas legales. | Alta |
| Email transaccional (SendGrid/SES) | Envio de emails. | Alta |
| SMS (Twilio/AWS SNS) | Notificaciones SMS. | Media |
| Almacenamiento (S3/GCS) | Imagenes, documentos. | Alta |
| Logistica / Envios (Coordinadora/Envia/Servientrega) | Tracking de envios. | Media |
| Analytics (Mixpanel/Amplitude) | Comportamiento de usuarios. | Baja |
| WhatsApp Business API | Notificaciones. | Baja |
| ERP contable | Sincronizacion contable. | Baja |
| Google Maps API | Geolocalizacion de la red. | Baja |

### Consideraciones de Rendimiento

- El calculo de comisiones binarias requiere recorrer todo el arbol. Para redes grandes (>100k nodos), usar acumuladores precalculados y colas de tareas asincronas.
- La visualizacion del arbol debe usar lazy loading y renderizar solo los nodos visibles.
- Los reportes pesados deben generarse en background y notificar al usuario cuando esten listos.
- Indices de base de datos optimizados para consultas de genealogia (nested sets, materialized paths o closure tables).

### Diagrama de Entidades (Alto Nivel)

```
Tenant (futuro)
  |
  ├── User (admin, soporte, etc.)
  ├── Affiliate
  │     ├── BinaryTree (position: left/right, parent_id)
  │     ├── SponsorTree (sponsor_id)
  │     ├── Rank (current, highest)
  │     ├── Wallet
  │     │     └── WalletTransaction
  │     ├── Order
  │     │     ├── OrderItem
  │     │     └── Payment
  │     ├── Commission
  │     │     └── CommissionDetail (by bonus type)
  │     ├── Autoship
  │     └── Volume (period, pv, bv_left, bv_right)
  │
  ├── Product
  │     ├── Category
  │     └── Kit
  │
  ├── Warehouse
  │     └── InventoryMovement
  │
  ├── LiquidationPeriod
  │     ├── LiquidationDetail
  │     └── LiquidationApproval
  │
  ├── CompensationPlan (config)
  │     ├── RankConfig
  │     ├── BonusConfig
  │     └── CapConfig
  │
  ├── Notification
  ├── AuditLog
  └── Invoice
```

---

## Entregable Actual (En Progreso)

> **Objetivo:** Un usuario con permisos (ej: gerente de ventas) puede iniciar sesion en el portal, ver los kits disponibles, inscribir un nuevo distribuidor seleccionando un paquete (ESP1=$195, ESP2=$495, ESP3=$995), y ver la confirmacion con el codigo generado (GH-SV-XXXXXX) y puntos asignados.

**Alcance del entregable:**
- [x] API: Autenticacion JWT (login, refresh, me)
- [x] API: RBAC con permisos granulares
- [x] API: Catalogo de productos/kits
- [x] API: Inscripcion de distribuidor (affiliate + orden + codigo + PV/BV)
- [x] API: Listado y detalle de distribuidores
- [x] API: Detalle de ordenes
- [ ] Frontend: Login del usuario administrativo
- [ ] Frontend: Vista de kits disponibles
- [ ] Frontend: Formulario de inscripcion de distribuidor
- [ ] Frontend: Confirmacion con codigo y datos del nuevo distribuidor

**Fuera de alcance para este entregable:** Arbol binario (colocacion/spillover), bonos, comisiones, billetera, genealogia.

---

## Roadmap de Desarrollo por Fases

### Fase 1 — MVP (Nucleo del Negocio)
> **Objetivo:** Tener una red operativa con calculo de comisiones funcional.

- [ ] Modulo de usuarios y afiliados (registro, perfil, estados).
- [ ] Estructura del arbol binario (colocacion, derrame).
- [ ] Arbol de patrocinio.
- [ ] Visualizacion de genealogia (arbol binario basico).
- [ ] Catalogo de productos y kits de inscripcion.
- [ ] Pedidos (inscripcion y re-compra).
- [ ] Calculo de BV/PV.
- [ ] Bono de patrocinio directo.
- [ ] Bono binario basico.
- [ ] Sistema de rangos (calificacion).
- [ ] Dashboard administrativo basico.
- [ ] Autenticacion y roles basicos (admin + afiliado).
- [ ] Auditoria basica.

### Fase 2 — Plan de Compensacion Completo
- [ ] Bono unilevel con compresion.
- [ ] Bono de liderazgo (matching).
- [ ] Bono de rango.
- [ ] Bono de inicio rapido.
- [ ] Topes progresivos por rango.
- [ ] Carry-over y flush.
- [ ] Proceso de liquidacion con aprobacion.
- [ ] Pre-liquidacion (preview).
- [ ] Billetera virtual basica.

### Fase 3 — Operaciones y Finanzas
- [ ] Auto-envio (autoship).
- [ ] Inventario multi-bodega.
- [ ] Integracion con pasarela de pago.
- [ ] Facturacion electronica.
- [ ] Retenciones fiscales.
- [ ] Reportes operativos completos.
- [ ] Exportacion PDF/Excel.

### Fase 4 — Comunicaciones y UX
- [ ] Notificaciones email transaccional.
- [ ] Notificaciones push.
- [ ] SMS.
- [ ] Portal del afiliado mejorado.
- [ ] Genealogia avanzada (mapa de calor, filtros).
- [ ] Simulador de comisiones.
- [ ] Impersonacion de afiliado.

### Fase 5 — Escala y SaaS
- [ ] Arquitectura multi-tenant.
- [ ] Branding por tenant.
- [ ] API publica.
- [ ] Integracion logistica.
- [ ] App movil / PWA.
- [ ] WhatsApp Business.
- [ ] Pool de liderazgo global.
- [ ] Eventos y capacitaciones.

---

## Registro de Avances

### 2026-02-13
- Creacion de la estructura de carpetas del proyecto.
- Redaccion del documento maestro `plan.md` v1.0 con reglas de negocio core.
- Creacion de `modulos.md` con el detalle funcional de los 13 modulos del sistema.
- Separacion de documentos: negocio en `plan.md` + `modulos.md`, tecnico en `context.md`.
- Documentos de negocio enviados a revision por el gerente de operaciones de Ganoherb.
- **Pendiente:** Feedback del gerente para ajustar valores, porcentajes y reglas.
- **Proximo paso:** Definir y comenzar desarrollo de los modulos esenciales de la Fase 1 (MVP).

### 2026-02-15
- Decisiones tecnicas definidas: pip+venv, SQLAlchemy+Alembic, Shadcn/ui+Tailwind, Docker Compose (solo Redis).
- Base de datos migrada a **Neon** (PostgreSQL 17 managed): instancia dev y prod separadas.
- Docker Compose ajustado a solo Redis (PostgreSQL ya no es local).
- Movidos `context.md` y `modulos.md` a `back_office_api/` (repo privado). `plan.md` permanece en `back_office_portal/` (repo publico, para revision del gerente).
- Creada estructura base del proyecto FastAPI: carpetas, .env (dev/prod), .gitignore, requirements.txt, config.py.
- **Completado:** Sub-fase 1.1 — Fundacion y Auth.

### 2026-02-16 — Sub-fase 1.1: Fundacion y Auth
- SQLAlchemy base model con UUID PKs, timestamps, tenant_id nullable (prep multi-tenant).
- Modelos: `User`, `Role`, `Permission`, `AuditLog` + tablas join `user_roles`, `role_permissions`.
- Relaciones many-to-many con `primaryjoin`/`secondaryjoin` explicitos (user_roles tiene 2 FKs a users: user_id y assigned_by).
- RBAC: `User.has_permission(codename)` + dependency `require_permission("resource:action")`.
- JWT auth: access token (15min) + refresh token (7 dias), passlib/bcrypt para hashing.
- Endpoints: `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`.
- Alembic configurado para async (asyncpg + Neon SSL via `connect_args`).
- Fix: asyncpg no acepta `sslmode`/`channel_binding` en query string — se limpia URL y pasa SSL via `ssl.create_default_context()`.
- Fix: passlib incompatible con bcrypt 5.x — fijado `bcrypt==4.0.1`.
- Seed: 5 roles del sistema, 17 permisos base, superadmin `admin@ganoherb.com.sv`.
- Primera migracion aplicada a Neon dev.
- SSH configurado para push a GitHub (ed25519).

### 2026-02-16 — Sub-fase 1.2: Affiliate Enrollment, Products, Orders
- Modelo `Affiliate`: datos personales, documentos (id_doc + tax_id), red MLM (sponsor_id separado de placement_parent_id + placement_side), acumuladores BV/PV, soft delete.
- Modelo `Product`: catalogo con soporte de kits (`is_kit`, `kit_tier`), PV/BV por producto.
- Modelos `Order` / `OrderItem`: ordenes con snapshot de precios al momento de compra, JSONB para shipping_address.
- Servicio de enrollment (`services/enrollment.py`): crea affiliate + orden de inscripcion en una sola transaccion. Validaciones: sponsor existe, posicion disponible, email unico, kit activo, al menos un documento.
- Generacion de codigo de distribuidor via secuencia PostgreSQL: `GH-SV-000001`.
- Generacion de numero de orden: `ORD-YYYYMMDD-XXXX`.
- Endpoints: `POST /affiliates/enroll`, `GET /affiliates`, `GET /affiliates/{id}`, `GET /products`, `GET /orders/{id}` — todos protegidos por permisos.
- Seed de kits: ESP1=$195 (PV:100, BV:100), ESP2=$495 (PV:300, BV:300), ESP3=$995 (PV:600, BV:600).
- Segunda migracion aplicada (affiliates, products, orders, order_items).
- Test end-to-end exitoso: login → listar kits → inscribir distribuidor → verificar datos.

### Endpoints disponibles (Fase 1 actual)
```
POST /api/v1/auth/login           — Autenticacion, retorna JWT tokens
POST /api/v1/auth/refresh         — Renovar tokens
GET  /api/v1/auth/me              — Perfil del usuario autenticado
POST /api/v1/affiliates/enroll    — Inscribir nuevo distribuidor + orden de kit
GET  /api/v1/affiliates           — Listar distribuidores (filtro por status)
GET  /api/v1/affiliates/{id}      — Detalle de distribuidor
GET  /api/v1/products             — Listar productos (filtro kits_only)
GET  /api/v1/orders/{id}          — Detalle de orden con items
GET  /health                      — Health check
```

### Proximos pasos (Entregable)
- Frontend: Setup del proyecto React + TypeScript + Shadcn/ui + Tailwind.
- Frontend: Pantalla de login.
- Frontend: Vista de kits disponibles.
- Frontend: Formulario de inscripcion de distribuidor.
- Frontend: Pantalla de confirmacion (codigo generado, datos, resumen de orden).

### Despues del entregable (Fase 1 continua)
- Sub-fase 1.3: Colocacion en arbol binario (derrame/spillover), visualizacion de genealogia.
- Sub-fase 1.4: Confirmacion de pago de orden → acreditar BV/PV al affiliate y su upline.
- Sub-fase 1.5: Bono de patrocinio directo.
