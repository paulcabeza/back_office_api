# Schema de Base de Datos — Fase 1 MVP

> **Version:** 1.0
> **Fecha:** 2026-02-15
> **Motor:** PostgreSQL 17 (Neon managed)
> **ORM:** SQLAlchemy 2.0 async + Alembic

---

## Convenciones Generales

- Todas las tablas usan `snake_case`.
- PKs: `id UUID DEFAULT gen_random_uuid()`.
- Timestamps: `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` (trigger on update).
- Soft delete: `deleted_at TIMESTAMPTZ NULL` donde aplique.
- Multi-tenant futuro: `tenant_id UUID NULL` en todas las tablas (nullable ahora, NOT NULL cuando se active multi-tenant). Indice parcial en cada tabla: `WHERE tenant_id IS NOT NULL`.
- Todas las FKs con `ON DELETE RESTRICT` salvo indicacion contraria.
- Enums almacenados como `VARCHAR` con CHECK constraint (no pg ENUM, para facilitar migraciones).

---

## 1. User

Usuarios internos del sistema (administradores, gerentes, soporte). **No** incluye afiliados/distribuidores — esos van en `affiliate`.

```
TABLE users
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
tenant_id           UUID        NULL FK -> tenants(id)
email               VARCHAR(255) NOT NULL
password_hash       VARCHAR(255) NOT NULL
first_name          VARCHAR(100) NOT NULL
last_name           VARCHAR(100) NOT NULL
is_active           BOOLEAN     NOT NULL DEFAULT true
is_superadmin       BOOLEAN     NOT NULL DEFAULT false
last_login_at       TIMESTAMPTZ NULL
failed_login_count  INT         NOT NULL DEFAULT 0
locked_until        TIMESTAMPTZ NULL
totp_secret         VARCHAR(255) NULL          -- 2FA secret (encrypted)
totp_enabled        BOOLEAN     NOT NULL DEFAULT false
created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
---------------------------------------------------------------
UNIQUE (tenant_id, email)   -- un email unico por tenant (o global si tenant_id IS NULL)
INDEX idx_users_email ON users(email)
INDEX idx_users_tenant ON users(tenant_id) WHERE tenant_id IS NOT NULL
```

**Decisiones:**
- `is_superadmin` para el super admin global (bypassea tenant). Solo 1-2 usuarios.
- Bloqueo de cuenta: `failed_login_count` >= threshold configurable -> `locked_until` se setea.
- 2FA: `totp_secret` almacenado encriptado (AES-256-GCM via app-level encryption). Obligatorio para admins, opcional para otros.

---

## 2. Role

Roles asignables a usuarios. RBAC con roles predefinidos + custom.

```
TABLE roles
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
tenant_id           UUID        NULL FK -> tenants(id)
name                VARCHAR(50) NOT NULL       -- 'admin', 'sales_manager', 'support', etc.
display_name        VARCHAR(100) NOT NULL
description         TEXT        NULL
is_system           BOOLEAN     NOT NULL DEFAULT false  -- roles del sistema no editables
created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
---------------------------------------------------------------
UNIQUE (tenant_id, name)
```

---

## 3. Permission

Permisos granulares del sistema. Formato: `resource:action` (ej: `affiliates:create`, `orders:read`).

```
TABLE permissions
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
codename            VARCHAR(100) NOT NULL UNIQUE  -- 'affiliates:create'
description         VARCHAR(255) NULL
resource            VARCHAR(50) NOT NULL          -- 'affiliates', 'orders', etc.
action              VARCHAR(50) NOT NULL          -- 'create', 'read', 'update', 'delete'
created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
---------------------------------------------------------------
INDEX idx_permissions_resource ON permissions(resource)
```

**Nota:** Los permisos son globales (no per-tenant). Se seedean con migracion.

---

## 4. RolePermission (join table)

```
TABLE role_permissions
---------------------------------------------------------------
role_id             UUID        NOT NULL FK -> roles(id) ON DELETE CASCADE
permission_id       UUID        NOT NULL FK -> permissions(id) ON DELETE CASCADE
---------------------------------------------------------------
PK (role_id, permission_id)
```

---

## 5. UserRole (join table)

```
TABLE user_roles
---------------------------------------------------------------
user_id             UUID        NOT NULL FK -> users(id) ON DELETE CASCADE
role_id             UUID        NOT NULL FK -> roles(id) ON DELETE CASCADE
assigned_at         TIMESTAMPTZ NOT NULL DEFAULT now()
assigned_by         UUID        NULL FK -> users(id)
---------------------------------------------------------------
PK (user_id, role_id)
```

---

## 6. Affiliate

Distribuidores/IBOs de la red MLM. Relacion 1:1 opcional con `users` (un admin puede no tener affiliate; un affiliate puede no tener user login en fase 1).

```
TABLE affiliates
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
tenant_id           UUID        NULL FK -> tenants(id)
user_id             UUID        NULL FK -> users(id) UNIQUE  -- 1:1 opcional
affiliate_code      VARCHAR(20) NOT NULL UNIQUE              -- 'GH-SV-000001'
country_code        VARCHAR(2)  NOT NULL DEFAULT 'SV'        -- ISO 3166-1 alpha-2

-- Datos personales
first_name          VARCHAR(100) NOT NULL
last_name           VARCHAR(100) NOT NULL
email               VARCHAR(255) NOT NULL
phone               VARCHAR(30)  NULL
date_of_birth       DATE         NULL
-- Documento de identidad personal (DUI en SV, Cedula en CO, INE en MX)
id_doc_type         VARCHAR(20)  NULL           -- 'DUI', 'CEDULA', 'INE', 'PASSPORT', etc.
id_doc_number       VARCHAR(50)  NULL

-- Documento de identificacion fiscal (NIT en SV/CO, RFC en MX, RUC en PE)
tax_id_type         VARCHAR(20)  NULL           -- 'NIT', 'RFC', 'RUC', 'RUT', etc.
tax_id_number       VARCHAR(50)  NULL

address_line1       VARCHAR(255) NULL
address_line2       VARCHAR(255) NULL
city                VARCHAR(100) NULL
state_province      VARCHAR(100) NULL
postal_code         VARCHAR(20)  NULL

-- Red MLM
sponsor_id          UUID        NULL FK -> affiliates(id)    -- patrocinador directo (immutable)
placement_parent_id UUID        NULL FK -> affiliates(id)    -- padre en arbol binario
placement_side      VARCHAR(5)  NULL CHECK (placement_side IN ('left', 'right'))
enrolled_at         TIMESTAMPTZ NOT NULL DEFAULT now()       -- fecha de inscripcion
kit_tier            VARCHAR(10) NULL CHECK (kit_tier IN ('ESP1', 'ESP2', 'ESP3'))

-- Estado y rango
status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'active', 'inactive', 'suspended', 'cancelled'))
current_rank        VARCHAR(30) NOT NULL DEFAULT 'affiliate'
highest_rank        VARCHAR(30) NOT NULL DEFAULT 'affiliate'

-- Acumuladores (se actualizan con cada orden pagada)
pv_current_period   DECIMAL(12,2) NOT NULL DEFAULT 0        -- PV del periodo actual
bv_left_total       DECIMAL(14,2) NOT NULL DEFAULT 0        -- BV acumulado pierna izq
bv_right_total      DECIMAL(14,2) NOT NULL DEFAULT 0        -- BV acumulado pierna der
bv_left_carry       DECIMAL(14,2) NOT NULL DEFAULT 0        -- carry-over pierna izq
bv_right_carry      DECIMAL(14,2) NOT NULL DEFAULT 0        -- carry-over pierna der

created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at          TIMESTAMPTZ NULL
---------------------------------------------------------------
UNIQUE (tenant_id, affiliate_code)
UNIQUE (tenant_id, email)
INDEX idx_affiliates_sponsor ON affiliates(sponsor_id)
INDEX idx_affiliates_placement ON affiliates(placement_parent_id, placement_side)
INDEX idx_affiliates_status ON affiliates(status)
INDEX idx_affiliates_tenant ON affiliates(tenant_id) WHERE tenant_id IS NOT NULL
INDEX idx_affiliates_code ON affiliates(affiliate_code)
```

**Decisiones clave:**

- **Sponsor vs Placement separados** (Regla #11): `sponsor_id` = quien refiere; `placement_parent_id` + `placement_side` = posicion en arbol binario. Ambos inmutables (Reglas #2 y #7) salvo admin con auditoria.
- **Codigo de distribuidor**: formato `GH-{COUNTRY}-{SEQ:06d}`. Generado por secuencia PostgreSQL per-country:
  ```sql
  CREATE SEQUENCE affiliate_seq_sv START 1;
  -- Al crear: 'GH-SV-' || LPAD(nextval('affiliate_seq_sv')::text, 6, '0')
  ```
- **Acumuladores BV**: denormalizados en la tabla para lectura rapida. Se actualizan transaccionalmente al confirmar pago de orden. El calculo de comisiones lee estos valores.
- **Arbol binario**: modelado con adjacency list (`placement_parent_id` + `placement_side`). Suficiente para Fase 1. Si el rendimiento lo requiere, se puede agregar materialized path o closure table despues.
- **`user_id` nullable**: en fase 1, los affiliates se crean desde el back office por un admin. El affiliate puede no tener login propio aun.
- **Rank values**: `'affiliate'`, `'bronze'`, `'silver'`, `'gold'`, `'platinum'`, `'diamond'`, `'double_diamond'`, `'crown'`, `'royal_crown'`, `'ambassador'`.
- **Soft delete**: `deleted_at` porque un affiliate cancelado mantiene su posicion en el arbol (Regla #8).
- **Documentos de identidad**: ambos pares (`id_doc_*` y `tax_id_*`) son nullable en BD, pero a nivel de servicio se valida que **al menos uno** sea proporcionado al crear/activar un afiliado. Esto permite flexibilidad (ej: un afiliado puede iniciar solo con DUI y agregar NIT despues), sin perder la garantia de tener al menos un documento de identificacion.

---

## 7. Product

Catalogo de productos incluyendo los kits de inscripcion ESP1/ESP2/ESP3.

```
TABLE products
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
tenant_id           UUID        NULL FK -> tenants(id)
sku                 VARCHAR(50) NOT NULL
name                VARCHAR(200) NOT NULL
description         TEXT        NULL
category            VARCHAR(50) NOT NULL DEFAULT 'general'

-- Precios
price_public        DECIMAL(10,2) NOT NULL       -- precio publico
price_distributor   DECIMAL(10,2) NOT NULL       -- precio para afiliados
currency            VARCHAR(3)  NOT NULL DEFAULT 'USD'

-- Volumenes
pv                  DECIMAL(8,2)  NOT NULL DEFAULT 0   -- Personal Volume
bv                  DECIMAL(8,2)  NOT NULL DEFAULT 0   -- Business Volume

-- Kit
is_kit              BOOLEAN     NOT NULL DEFAULT false
kit_tier            VARCHAR(10) NULL CHECK (kit_tier IN ('ESP1', 'ESP2', 'ESP3'))

-- Estado
status              VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'discontinued'))
country_availability VARCHAR(2)[] NOT NULL DEFAULT '{SV}'  -- paises donde esta disponible

-- Inventario basico (stock real va en modulo de inventario en fase posterior)
track_stock         BOOLEAN     NOT NULL DEFAULT false
stock_quantity      INT         NOT NULL DEFAULT 0

created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
---------------------------------------------------------------
UNIQUE (tenant_id, sku)
INDEX idx_products_kit ON products(is_kit) WHERE is_kit = true
INDEX idx_products_status ON products(status)
INDEX idx_products_tenant ON products(tenant_id) WHERE tenant_id IS NOT NULL
```

**Seed data — Kits de inscripcion:**

| SKU | Nombre | Precio | PV | BV | kit_tier |
|-----|--------|--------|----|----|----------|
| KIT-ESP1 | Kit Especial 1 | $195.00 | 100 | 100 | ESP1 |
| KIT-ESP2 | Kit Especial 2 | $495.00 | 300 | 300 | ESP2 |
| KIT-ESP3 | Kit Especial 3 | $995.00 | 600 | 600 | ESP3 |

> **Nota:** Los valores de PV/BV son estimados. Pendiente confirmacion del gerente de operaciones. Seran configurables via admin panel.

---

## 8. Order

Registro de compras. En Fase 1 solo manejaremos ordenes de inscripcion (compra de kit).

```
TABLE orders
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
tenant_id           UUID        NULL FK -> tenants(id)
order_number        VARCHAR(30) NOT NULL UNIQUE              -- autogenerado: 'ORD-20260215-XXXX'
affiliate_id        UUID        NOT NULL FK -> affiliates(id)
order_type          VARCHAR(20) NOT NULL DEFAULT 'enrollment'
                    CHECK (order_type IN ('enrollment', 'repurchase', 'autoship', 'admin'))
status              VARCHAR(20) NOT NULL DEFAULT 'pending_payment'
                    CHECK (status IN (
                        'pending_payment',
                        'paid',
                        'in_preparation',
                        'shipped',
                        'delivered',
                        'cancelled',
                        'returned'
                    ))

-- Totales
subtotal            DECIMAL(10,2) NOT NULL DEFAULT 0
tax_amount          DECIMAL(10,2) NOT NULL DEFAULT 0
shipping_amount     DECIMAL(10,2) NOT NULL DEFAULT 0
discount_amount     DECIMAL(10,2) NOT NULL DEFAULT 0
total               DECIMAL(10,2) NOT NULL DEFAULT 0

-- Volumenes totales de la orden
total_pv            DECIMAL(10,2) NOT NULL DEFAULT 0
total_bv            DECIMAL(10,2) NOT NULL DEFAULT 0

-- Pago
payment_method      VARCHAR(30) NULL    -- 'cash', 'card', 'transfer', 'wallet'
payment_reference   VARCHAR(100) NULL   -- referencia externa del pago
paid_at             TIMESTAMPTZ NULL

-- Envio
shipping_address    JSONB       NULL     -- {line1, line2, city, state, postal_code, country}
tracking_number     VARCHAR(100) NULL

-- Metadata
notes               TEXT        NULL
created_by          UUID        NOT NULL FK -> users(id)     -- usuario admin que creo la orden
created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
---------------------------------------------------------------
INDEX idx_orders_affiliate ON orders(affiliate_id)
INDEX idx_orders_status ON orders(status)
INDEX idx_orders_type ON orders(order_type)
INDEX idx_orders_created ON orders(created_at)
INDEX idx_orders_tenant ON orders(tenant_id) WHERE tenant_id IS NOT NULL
```

**Decisiones:**
- **BV solo de pedidos pagados** (Regla #4): los acumuladores de BV/PV en `affiliates` solo se actualizan cuando `status` cambia a `'paid'`. La logica vive en el servicio, no en trigger.
- **`created_by`**: siempre el usuario admin que creo la orden. En fase 1 todo se hace desde el back office.
- **`shipping_address` como JSONB**: flexibilidad para distintos formatos de direccion por pais, sin tablas extra en MVP.

---

## 9. OrderItem

Detalle de productos en cada orden.

```
TABLE order_items
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
order_id            UUID        NOT NULL FK -> orders(id) ON DELETE CASCADE
product_id          UUID        NOT NULL FK -> products(id)
quantity            INT         NOT NULL DEFAULT 1 CHECK (quantity > 0)
unit_price          DECIMAL(10,2) NOT NULL       -- precio al momento de la compra
pv                  DECIMAL(8,2)  NOT NULL        -- PV del producto al momento
bv                  DECIMAL(8,2)  NOT NULL        -- BV del producto al momento
line_total          DECIMAL(10,2) NOT NULL        -- unit_price * quantity
line_pv             DECIMAL(10,2) NOT NULL        -- pv * quantity
line_bv             DECIMAL(10,2) NOT NULL        -- bv * quantity
---------------------------------------------------------------
INDEX idx_order_items_order ON order_items(order_id)
INDEX idx_order_items_product ON order_items(product_id)
```

**Nota:** Se copian `unit_price`, `pv`, `bv` del producto al momento de la compra (snapshot). Si el producto cambia de precio/puntos despues, las ordenes historicas no se ven afectadas.

---

## 10. AuditLog

Log inmutable de todas las acciones del sistema. Append-only (Regla #9).

```
TABLE audit_logs
---------------------------------------------------------------
id                  UUID        PK DEFAULT gen_random_uuid()
tenant_id           UUID        NULL
user_id             UUID        NULL FK -> users(id)          -- quien realizo la accion
action              VARCHAR(50) NOT NULL                      -- 'affiliate.create', 'order.pay', etc.
resource_type       VARCHAR(50) NOT NULL                      -- 'affiliate', 'order', 'user'
resource_id         UUID        NULL                          -- id del registro afectado
old_values          JSONB       NULL                          -- valores anteriores (para updates)
new_values          JSONB       NULL                          -- valores nuevos
ip_address          INET        NULL
user_agent          VARCHAR(500) NULL
reason              TEXT        NULL                          -- justificacion (obligatoria en acciones admin manuales)
created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
---------------------------------------------------------------
INDEX idx_audit_action ON audit_logs(action)
INDEX idx_audit_resource ON audit_logs(resource_type, resource_id)
INDEX idx_audit_user ON audit_logs(user_id)
INDEX idx_audit_created ON audit_logs(created_at)
INDEX idx_audit_tenant ON audit_logs(tenant_id) WHERE tenant_id IS NOT NULL
```

**Decisiones:**
- **Append-only**: no hay `updated_at` ni `deleted_at`. Ningun endpoint permite UPDATE o DELETE en esta tabla.
- **Retencion minimo 5 anos** (requisito de context.md). Se implementara particionamiento por fecha cuando el volumen lo justifique.
- **`old_values`/`new_values` como JSONB**: flexible para cualquier entidad, sin necesidad de columnas especificas por tipo.
- **`reason` obligatorio** para acciones manuales de admin (mover afiliado, cambiar estado, ajuste de comision). Validado a nivel de servicio.

---

## Diagrama de Relaciones

```
users 1--N user_roles N--1 roles 1--N role_permissions N--1 permissions
  |
  |-- 1:1 (opcional) --> affiliates
  |-- 1:N (created_by) --> orders
  |-- 1:N (user_id) --> audit_logs

affiliates
  |-- self-ref (sponsor_id) --> affiliates        [arbol de patrocinio]
  |-- self-ref (placement_parent_id) --> affiliates [arbol binario]
  |-- 1:N --> orders

orders 1--N order_items N--1 products

audit_logs (standalone, append-only)
```

---

## Validacion contra Reglas de Negocio Inviolables

| # | Regla | Soporte en Schema |
|---|-------|-------------------|
| 1 | Un afiliado, una posicion | `UNIQUE(placement_parent_id, placement_side)` impide duplicados. Un affiliate tiene exactamente un `placement_parent_id` + `placement_side`. |
| 2 | Sin retroceso de posicion | `placement_parent_id` y `placement_side` inmutables a nivel de servicio. Cambios solo via admin con audit_log obligatorio. |
| 3 | Calificacion antes de comision | Los campos `current_rank`, `pv_current_period` existen para validacion pre-pago. (Comisiones en fases posteriores.) |
| 4 | BV solo de pedidos pagados | Acumuladores BV se actualizan solo en transicion `orders.status -> 'paid'`. Logica en servicio. |
| 5 | Reverso en devolucion | `orders.status = 'returned'` dispara reverso de BV/PV. Logica en servicio. |
| 6 | Topes absolutos | Campos de rango + configuracion de topes (fase 2). Schema lo soporta via `current_rank`. |
| 7 | Patrocinador inmutable | `sponsor_id` inmutable a nivel de servicio. Solo admin con razon + audit_log. |
| 8 | Integridad del arbol | FKs + constraints + soft delete (no se borra un affiliate, se cancela). |
| 9 | Auditoria obligatoria | Tabla `audit_logs` append-only con `old_values`/`new_values`, `reason`, `ip_address`. |
| 10 | Comisiones no editables post-pago | (Fase 2 — tabla de comisiones tendra campo `is_disbursed` inmutable.) |
| 11 | Separacion sponsor/placement | Campos separados: `sponsor_id` (patron de patrocinio) vs `placement_parent_id` + `placement_side` (arbol binario). |
| 12 | Periodos cerrados inmutables | (Fase 2 — tabla `liquidation_periods` con `is_closed` flag.) |

---

## Secuencias para Codigos

```sql
-- Secuencia para codigos de afiliado por pais
CREATE SEQUENCE affiliate_seq_sv START 1 INCREMENT 1;
-- Uso: 'GH-SV-' || LPAD(nextval('affiliate_seq_sv')::text, 6, '0')
-- Resultado: GH-SV-000001, GH-SV-000002, ...

-- Secuencia para numeros de orden
CREATE SEQUENCE order_seq START 1 INCREMENT 1;
-- Uso: 'ORD-' || TO_CHAR(now(), 'YYYYMMDD') || '-' || LPAD(nextval('order_seq')::text, 4, '0')
```

---

## Seed Data Inicial

### Roles del sistema

| name | display_name | is_system |
|------|-------------|-----------|
| super_admin | Super Administrador | true |
| admin | Administrador | true |
| sales_manager | Gerente de Ventas | true |
| operations_manager | Gerente de Operaciones | true |
| support | Soporte | true |

### Permisos base (Fase 1)

| codename | resource | action |
|----------|----------|--------|
| affiliates:create | affiliates | create |
| affiliates:read | affiliates | read |
| affiliates:update | affiliates | update |
| affiliates:delete | affiliates | delete |
| orders:create | orders | create |
| orders:read | orders | read |
| orders:update | orders | update |
| products:read | products | read |
| products:create | products | create |
| products:update | products | update |
| users:create | users | create |
| users:read | users | read |
| users:update | users | update |
| users:delete | users | delete |
| roles:read | roles | read |
| roles:manage | roles | manage |
| audit:read | audit | read |

### Productos (kits)

Ver tabla en seccion de Product arriba.

---

## Indices de Integridad Adicionales

```sql
-- Evitar que un affiliate tenga dos hijos en la misma pierna
CREATE UNIQUE INDEX idx_unique_placement
ON affiliates(placement_parent_id, placement_side)
WHERE placement_parent_id IS NOT NULL AND deleted_at IS NULL;

-- Evitar auto-referencia directa en sponsor
ALTER TABLE affiliates ADD CONSTRAINT chk_no_self_sponsor
CHECK (sponsor_id IS DISTINCT FROM id);

-- Evitar auto-referencia directa en placement
ALTER TABLE affiliates ADD CONSTRAINT chk_no_self_placement
CHECK (placement_parent_id IS DISTINCT FROM id);
```

---

## Notas para Implementacion

1. **Migraciones**: usar Alembic. El archivo `schema.md` es la referencia de diseno; el codigo vive en `app/models/`.
2. **SQLAlchemy models**: un archivo por entidad en `app/models/` (ej: `user.py`, `affiliate.py`, `product.py`, `order.py`, `audit_log.py`).
3. **Base model comun**: crear `BaseModel` con `id`, `created_at`, `updated_at`, `tenant_id`. Todas las entidades heredan.
4. **Audit log**: implementar como middleware/decorator que captura automaticamente `old_values`/`new_values` en cada mutacion.
5. **Transacciones**: la creacion de affiliate + order de inscripcion + acreditacion de BV debe ser **una sola transaccion** para garantizar consistencia.
6. **Affiliate code**: generar en la capa de servicio usando la secuencia de PostgreSQL, no en el ORM.
