# Ganoherb Back Office — Contexto Tecnico y Bitacora de Progreso

> **Empresa:** Ganoherb
> **Pais inicial:** El Salvador (expansion futura a otros paises)

## Convenciones de Git

- **No agregar co-autor de Claude en los commits.** Los commits son del desarrollador unicamente.

## Convenciones de Documentacion

- **Todo el contexto tecnico y progreso debe quedar en archivos versionados en Git** (`context.md`, `schema.md`, `flujos.md`, `modulos.md`, `plan.md`), no en memorias locales de herramientas. El equipo trabaja desde multiples maquinas y las memorias locales no se sincronizan.
- `context.md` es la fuente de verdad para decisiones tecnicas, infraestructura, known issues y bitacora de avances.
- Al finalizar una sesion de trabajo, **siempre actualizar context.md** con los cambios realizados.

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
| **Frontend** | React + TypeScript (Vite) |
| **Estado Frontend** | Zustand |
| **Routing Frontend** | React Router v7 |
| **HTTP Client** | Axios |
| **UI Components** | Shadcn/ui + Tailwind CSS |
| **Autenticacion** | JWT (access + refresh tokens) |
| **Dependencias Python** | pip + venv (requirements.txt) |
| **Almacenamiento** | AWS S3 / MinIO |
| **Email** | SendGrid / AWS SES |
| **Despliegue** | Docker + Docker Compose, Linode Nanode 1GB (prod) |
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
- **Git:** Identidad configurada per-repo (no global). SSH auth con ed25519. Remote: `git@github.com:paulcabeza/back_office_api.git`. Frontend remote: `https://github.com/paulcabeza/back_office_portal.git`.
- **venv:** En `.venv/` dentro de `back_office_api/`. Python 3.12.
- **Shell `!` en bash:** Causa problemas de escaping — usar scripts Python para testing en vez de curl con passwords.
- **`npm create vite@latest .`:** Falla si el directorio no esta vacio — usar temp dir y copiar archivos.
- **Frontend client.ts:** URL base usa `import.meta.env.VITE_API_BASE_URL || "/api/v1"`. En dev local usar `.env` con `VITE_API_BASE_URL=http://localhost:8000/api/v1`.

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
POST  /api/v1/auth/login           — Autenticacion, retorna JWT tokens
POST  /api/v1/auth/refresh         — Renovar tokens
GET   /api/v1/auth/me              — Perfil del usuario autenticado
POST  /api/v1/users                — Crear usuario admin/staff
GET   /api/v1/users                — Listar usuarios (paginacion)
GET   /api/v1/users/roles          — Listar roles disponibles (para dropdowns)
GET   /api/v1/users/{id}           — Detalle de usuario
PATCH /api/v1/users/{id}           — Actualizar usuario (nombre, email, rol, estado)
POST  /api/v1/affiliates/enroll    — Inscribir nuevo distribuidor + orden de kit
GET   /api/v1/affiliates           — Listar distribuidores (filtro por status)
GET   /api/v1/affiliates/{id}      — Detalle de distribuidor
GET   /api/v1/affiliates/{id}/tree — Arbol binario desde un nodo (depth configurable)
GET   /api/v1/products             — Listar productos (filtro kits_only)
GET   /api/v1/orders/{id}              — Detalle de orden con items
PATCH /api/v1/orders/{id}/confirm-payment — Confirmar pago, acreditar BV/PV, activar distribuidor
GET   /health                            — Health check
```

### Plan del Frontend (Entregable)

**Decisiones tecnicas:**
- Vite + React + TypeScript, npm como gestor de paquetes.
- Zustand para estado global (auth: tokens, usuario, login/logout).
- React Router v7 para navegacion, rutas protegidas con componente `ProtectedRoute`.
- Axios con interceptores para auth (Bearer token) y refresh automatico (patron de cola de retry en 401).
- Shadcn/ui + Tailwind CSS para UI. Componentes instalados via CLI.
- Formularios controlados con `useState` y validacion manual (sin react-hook-form/zod — un solo formulario no justifica la dependencia).
- Labels en espanol, codigo en ingles. Sin i18n formal (solo mercado SV por ahora).
- Tokens en `localStorage` (back office interno, riesgo XSS aceptable).
- API retorna Decimals como strings; parsear con `Number()` al recibir.

**Estructura de carpetas:**
```
back_office_portal/src/
  main.tsx, App.tsx, index.css
  api/
    client.ts           — Axios instance + interceptors (auth, refresh, 401 retry queue)
    auth.ts             — login(), refreshToken(), getMe()
    products.ts         — getKits()
    affiliates.ts       — enrollAffiliate()
  stores/
    auth-store.ts       — Zustand: tokens, user, isAuthenticated, login/logout, initialize
  types/
    auth.ts             — LoginRequest, TokenResponse, User, Role
    product.ts          — Product
    affiliate.ts        — EnrollmentRequest, AffiliateResponse
    order.ts            — OrderResponse, OrderItemResponse, EnrollmentResponse
  lib/
    utils.ts            — cn(), formatCurrency(), formatDate()
  components/
    ui/                 — Shadcn (auto-generated)
    layout/
      app-layout.tsx    — Shell: header + Outlet
      header.tsx        — User info + logout
    shared/
      protected-route.tsx
      loading-spinner.tsx
  pages/
    login/login-page.tsx
    enrollment/
      kit-selection-page.tsx
      enrollment-form-page.tsx
      confirmation-page.tsx
```

**Rutas:**
| Path | Componente | Auth |
|------|-----------|------|
| `/login` | LoginPage | No |
| `/enrollment/kits` | KitSelectionPage | Si |
| `/enrollment/form` | EnrollmentFormPage | Si |
| `/enrollment/confirmation` | ConfirmationPage | Si |
| `/` | Redirect a `/enrollment/kits` | Si |

**Pantallas:**
1. **Login** — Card centrado, email + password, errores inline (401→credenciales, 423→bloqueado). Redirige a `/enrollment/kits`.
2. **Seleccion de Kit** — Grid de 3 cards (ESP1=$195, ESP2=$495, ESP3=$995) con PV/BV como badges. Al seleccionar → navigate con state al form.
3. **Formulario de Inscripcion** — Kit seleccionado (readonly), datos personales, documentos (al menos 1 par requerido: id_doc O tax_id), direccion, patrocinador (opcional). Submit → POST /affiliates/enroll → navigate a confirmacion.
4. **Confirmacion** — Codigo de distribuidor (GH-SV-XXXXXX resaltado), datos del afiliado, resumen de orden con PV/BV y total, boton "Inscribir Otro".

**Orden de implementacion:**
1. Init proyecto (Vite + deps + Tailwind + Shadcn)
2. Tipos TypeScript (`types/*.ts`)
3. API client (`api/client.ts` con Axios + request interceptor)
4. Auth store (`stores/auth-store.ts` con Zustand + localStorage)
5. API auth (`api/auth.ts`)
6. Protected route + Router + App.tsx
7. Login page (primera pantalla funcional end-to-end)
8. Refresh interceptor (completar `client.ts` con cola de retry)
9. Layout (app-layout + header)
10. API products + Kit selection page
11. API affiliates + Enrollment form page
12. Confirmation page

### 2026-02-22 — Documentacion de Flujos + Enrollment crea User

- Creado `back_office_api/flujos.md`: 10 flujos operativos detallados del MVP (login, inscripcion, pago, genealogia, bonos, etc.).
- Agregado resumen simplificado de flujos en `back_office_portal/plan.md` seccion 7 (version para gerencia, sin detalles tecnicos).
- **Enrollment modificado para crear User + Affiliate:**
  - Nuevo campo `password` (min 8 chars) en `EnrollmentRequest`.
  - El servicio ahora crea un `User` (con password hasheada bcrypt) y le asigna rol `distributor`, antes de crear el `Affiliate` vinculado via `user_id`.
  - Validacion de unicidad de email ahora verifica en ambas tablas (`users` y `affiliates`).
- Nuevo rol `distributor` agregado al seed (permisos: `affiliates:read`, `orders:read`, `products:read`).
- Seed ejecutado: 6 roles en BD (antes 5).
- Decisiones del frontend documentadas en context.md: Vite, Zustand, React Router v7, Axios, Shadcn/ui.
- Proveedor de email: SendGrid integrado.
- **SendGrid integrado:**
  - `app/services/email.py`: funciones `send_welcome_distributor()` y `send_enrollment_notification_admin()`.
  - Config: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `SENDGRID_FROM_NAME`, `SENDGRID_ENABLED` (false en dev, loguea en consola).
  - Se llama desde el endpoint de enrollment (no bloquea, errores se loguean).
  - Pendiente: configurar API key de SendGrid y activar (`SENDGRID_ENABLED=true`).
- **Endpoint de confirmacion de pago implementado:**
  - `PATCH /api/v1/orders/{id}/confirm-payment` (permiso `orders:update`).
  - Recibe `payment_method` y `payment_reference`.
  - En una transaccion: marca orden como `paid`, acredita PV al distribuidor, acredita BV a toda la linea ascendente del arbol binario, activa distribuidor si es orden de inscripcion.
  - Servicio `app/services/payment.py` con funcion `_accrue_bv_to_upline()` que recorre el arbol hacia arriba.
- **Endpoint de arbol binario implementado:**
  - `GET /api/v1/affiliates/{id}/tree?depth=3` (permiso `affiliates:read`).
  - Retorna estructura recursiva: cada nodo tiene `left_child` y `right_child` con datos del distribuidor.
  - Servicio `app/services/tree.py` con funciones `get_binary_tree()` y `_build_node()`.
  - Profundidad configurable (1-10, default 3).
- **Frontend iniciado:**
  - Proyecto Vite + React + TypeScript creado en `back_office_portal/`.
  - Node.js 22 LTS instalado via nvm.
  - Pendiente: instalar dependencias (Tailwind, Shadcn, Zustand, React Router, Axios), crear estructura de carpetas y pantallas.

### 2026-02-22 — Deploy a Produccion (Linode)

- **Servidor:** Linode Nanode 1GB ($5/mes), Ubuntu 24.04 LTS, IP `96.126.117.59`.
- **Arquitectura en produccion:**
  - Nginx (Alpine): reverse proxy + sirve SPA estatica.
  - Backend: imagen Docker en GHCR (`ghcr.io/paulcabeza/back_office_api:latest`), uvicorn 1 worker.
  - Redis 7 (Alpine): cache sin persistencia, 32MB max.
  - Frontend: archivos estaticos en `/opt/ganoherb/portal/` (NO es container).
  - DB: PostgreSQL 17 en Neon (instancia de produccion separada de dev).
- **Estructura en servidor:** `/opt/ganoherb/` con `docker-compose.yml`, `.env`, `nginx/conf.d/default.conf`, `portal/`.
- **CI/CD con GitHub Actions:**
  - Backend (`back_office_api`): push a master → build imagen Docker → push a GHCR → SSH al Linode → `docker compose pull && up -d` → `alembic upgrade head`.
  - Portal (`back_office_portal`): push a master → `npm ci && npm run build` (con `VITE_API_BASE_URL=/api/v1`) → SCP `dist/*` a `/opt/ganoherb/portal/`.
- **GitHub Secrets** configurados en ambos repos: `LINODE_HOST`, `LINODE_USER`, `LINODE_SSH_KEY`.
- **Archivos creados:**
  - `back_office_api/Dockerfile` — python:3.12-slim, uvicorn 1 worker.
  - `back_office_api/.dockerignore`
  - `back_office_api/.github/workflows/deploy.yml`
  - `back_office_portal/.github/workflows/deploy.yml`
  - `deploy/` (en root del monorepo, referencia): `docker-compose.yml`, `nginx/conf.d/default.conf`, `.env.example`, `setup-server.sh`.
- **Cambios al frontend:**
  - `client.ts`: URL base cambiada de hardcoded `localhost:8000` a `import.meta.env.VITE_API_BASE_URL || "/api/v1"`.
  - `.env` local creado con `VITE_API_BASE_URL=http://localhost:8000/api/v1` (en `.gitignore`).
- **Servidor configurado:** swap 1GB, Docker, UFW (22/80/443), usuario `deploy` con acceso SSH y grupo docker.
- **Primer deploy exitoso:** ambos workflows completados, 3 containers corriendo, `/health` → OK, SPA cargando, API respondiendo via proxy.
- **Seed ejecutado en produccion:** 3 roles (super_admin, admin, distributor), 17 permisos, 3 kits, superadmin.
- **Dominios planificados (pendiente DNS):**
  - `ganoherb.com.sv` → WordPress (sitio principal, futuro).
  - `backoffice.ganoherb.com.sv` → SPA + API.

### 2026-02-23 — CRUD de Usuarios + created_by + Color Ganoherb

- **CRUD de Usuarios implementado** — 4 endpoints nuevos:
  - `POST /api/v1/users` — Crear usuario admin/staff (permiso `users:create`). Hashea password, asigna roles, valida email unico, bloquea asignacion de super_admin.
  - `GET /api/v1/users` — Listar usuarios con paginacion (permiso `users:read`).
  - `GET /api/v1/users/{id}` — Detalle de usuario (permiso `users:read`).
  - `PATCH /api/v1/users/{id}` — Actualizar nombre, email, is_active, rol (permiso `users:update`). Protege superadmins.
- **Schemas nuevos:** `UpdateUserRequest`, `UserListResponse` en `app/schemas/auth.py`. Se reutilizo `UserCreate` existente para el POST.
- **`created_by_user_id` agregado a Affiliate:**
  - Nueva columna `created_by_user_id` (UUID FK a users, nullable) en modelo `Affiliate`.
  - Enrollment service (`services/enrollment.py`) ahora pasa `created_by_user_id` al crear el affiliate.
  - Campo expuesto en `AffiliateResponse` schema.
  - Migracion Alembic: `a3f1c8d92e01_add_created_by_user_id_to_affiliates.py`.
- **`GET /users/roles`** — endpoint adicional para obtener roles disponibles (usado en dropdowns del frontend).
- **Frontend — Pantallas de gestion de usuarios:**
  - `/users` — tabla con lista de usuarios (nombre, email, rol, estado, fecha), botones editar y activar/desactivar.
  - `/users/new` — formulario para crear usuario (nombre, apellido, email, contraseña, selector de rol).
  - `/users/:userId/edit` — formulario pre-llenado para editar datos, cambiar rol, activar/desactivar.
  - Card "Gestion de Usuarios" en el dashboard **solo visible para superadmins** (`user.is_superadmin`).
  - Archivos nuevos: `types/user.ts`, `api/users.ts`, `pages/users/users-page.tsx`, `pages/users/create-user-page.tsx`, `pages/users/edit-user-page.tsx`.
- **Color primario del frontend cambiado** de teal (`oklch(0.432 0.1 155)`) a rojo coral Ganoherb `#e9514b` (`oklch(0.588 0.18 25)`). Destructive diferenciado a rojo oscuro (`oklch(0.45 0.22 30)`).
- Router registrado en `app/api/v1/router.py`.
- **Roles simplificados a 3** (antes eran 6):
  - `super_admin` (Super Administrador) — acceso total, unico rol que puede gestionar usuarios (`users:*`).
  - `admin` (Administrador) — acceso operativo: afiliados, ordenes, productos, audit. NO puede crear/editar usuarios.
  - `distributor` (Distribuidor) — solo lectura (se asigna automaticamente al inscribir).
  - Eliminados: `sales_manager`, `operations_manager`, `support` (innecesarios para MVP).
  - Seed actualizado con limpieza de roles obsoletos y reasignacion de permisos del admin.
- **Workflow del portal corregido** — se agrega `docker compose restart nginx` despues del SCP para evitar 403 por cache de volumen.
- **Seed ejecutado en produccion** — roles limpiados, migracion aplicada via CI/CD.
- **Proteccion de auto-desactivacion** — endpoint PATCH /users/{id} impide que un usuario se desactive a si mismo.
- **`GET /affiliates/me`** — nuevo endpoint que retorna el perfil de distribuidor del usuario autenticado (busca por `user_id`). No requiere permiso especifico, solo autenticacion.
- **Dashboard inteligente por rol:**
  - Distribuidores ven su dashboard con: codigo, estado, PV periodo, BV izq/der, rango, info personal.
  - Admins/superadmins ven el menu administrativo (inscripcion, gestion usuarios, etc.).
  - Componente `SmartDashboard` en App.tsx decide segun roles del usuario.
- **Username auto-generado al crear usuarios:**
  - Campo `username` (String(50), unique, nullable) agregado al modelo User. Migracion `b7e2d4f10a83`.
  - Logica: primera letra del primer nombre + primer apellido (ej: "Rosa Cabrera Romero" → `rcabrera`). Si existe, agrega inicial del segundo apellido (`rcabrerar`). Si aun existe, sufijo numerico (`rcabrera1`).
  - Acentos removidos via `unicodedata.normalize("NFKD")`.
  - Login acepta username o email (`LoginRequest.email` ahora es `str`, no `EmailStr`). Busca con `OR(email, username)`.
  - Frontend: login muestra "Usuario o correo electronico", tabla de usuarios muestra columna "Usuario".
- **Vista de lista de usuarios mejorada:** columna Email removida (solo se muestra Username). La lista es mas limpia: Nombre, Usuario, Rol, Estado, Creado, Acciones.
- **Vista de edicion de usuario mejorada:** username se muestra como campo readonly con icono de User y nota "Generado automaticamente, no se puede modificar". Subtitulo muestra `@username` junto al nombre completo.
- **Preview de username en creacion:** al escribir nombre/apellido, se genera y muestra el username estimado en tiempo real (campo readonly). Tras crear el usuario, pantalla de confirmacion muestra el username real generado por el backend.

### Despues del entregable (Fase 1 continua)
- Sub-fase 1.3: Colocacion en arbol binario (derrame/spillover automatico).
- Sub-fase 1.5: Bono de patrocinio directo.
