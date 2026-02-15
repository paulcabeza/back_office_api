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
- **En progreso:** Sub-fase 1.1 — Fundacion y Auth (base models, SQLAlchemy async, JWT, User model, auth endpoints).
