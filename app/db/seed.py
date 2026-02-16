"""
Seed script: populates the database with initial roles, permissions, and superadmin user.

Usage:
    python -m app.db.seed
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.models.associations import role_permissions
from app.models.audit_log import AuditLog
from app.models.role import Permission, Role
from app.models.user import User

# --- Seed data ---

ROLES = [
    {"name": "super_admin", "display_name": "Super Administrador", "is_system": True},
    {"name": "admin", "display_name": "Administrador", "is_system": True},
    {"name": "sales_manager", "display_name": "Gerente de Ventas", "is_system": True},
    {"name": "operations_manager", "display_name": "Gerente de Operaciones", "is_system": True},
    {"name": "support", "display_name": "Soporte", "is_system": True},
]

PERMISSIONS = [
    # Affiliates
    {"codename": "affiliates:create", "resource": "affiliates", "action": "create", "description": "Create new affiliates"},
    {"codename": "affiliates:read", "resource": "affiliates", "action": "read", "description": "View affiliates"},
    {"codename": "affiliates:update", "resource": "affiliates", "action": "update", "description": "Update affiliate data"},
    {"codename": "affiliates:delete", "resource": "affiliates", "action": "delete", "description": "Deactivate/cancel affiliates"},
    # Orders
    {"codename": "orders:create", "resource": "orders", "action": "create", "description": "Create orders"},
    {"codename": "orders:read", "resource": "orders", "action": "read", "description": "View orders"},
    {"codename": "orders:update", "resource": "orders", "action": "update", "description": "Update order status"},
    # Products
    {"codename": "products:read", "resource": "products", "action": "read", "description": "View products"},
    {"codename": "products:create", "resource": "products", "action": "create", "description": "Create products"},
    {"codename": "products:update", "resource": "products", "action": "update", "description": "Update products"},
    # Users
    {"codename": "users:create", "resource": "users", "action": "create", "description": "Create admin users"},
    {"codename": "users:read", "resource": "users", "action": "read", "description": "View admin users"},
    {"codename": "users:update", "resource": "users", "action": "update", "description": "Update admin users"},
    {"codename": "users:delete", "resource": "users", "action": "delete", "description": "Deactivate admin users"},
    # Roles
    {"codename": "roles:read", "resource": "roles", "action": "read", "description": "View roles"},
    {"codename": "roles:manage", "resource": "roles", "action": "manage", "description": "Manage role assignments"},
    # Audit
    {"codename": "audit:read", "resource": "audit", "action": "read", "description": "View audit logs"},
]

# Roles that get ALL permissions
FULL_ACCESS_ROLES = ["super_admin", "admin"]

# Role-specific permissions for non-admin roles
ROLE_PERMISSIONS = {
    "sales_manager": [
        "affiliates:create", "affiliates:read", "affiliates:update",
        "orders:create", "orders:read", "orders:update",
        "products:read",
    ],
    "operations_manager": [
        "affiliates:read", "affiliates:update",
        "orders:read", "orders:update",
        "products:read", "products:create", "products:update",
        "users:read",
        "audit:read",
    ],
    "support": [
        "affiliates:read",
        "orders:read",
        "products:read",
    ],
}

SUPERADMIN_EMAIL = "admin@ganoherb.com.sv"
SUPERADMIN_PASSWORD = "Admin2026!"  # Change immediately after first login


async def seed_database():
    async with async_session_factory() as db:
        # 1. Seed permissions
        print("Seeding permissions...")
        perm_map: dict[str, Permission] = {}
        for perm_data in PERMISSIONS:
            result = await db.execute(
                select(Permission).where(Permission.codename == perm_data["codename"])
            )
            perm = result.scalar_one_or_none()
            if perm is None:
                perm = Permission(**perm_data)
                db.add(perm)
                await db.flush()
            perm_map[perm.codename] = perm
        print(f"  {len(perm_map)} permissions ready.")

        # 2. Seed roles
        print("Seeding roles...")
        role_map: dict[str, Role] = {}
        for role_data in ROLES:
            result = await db.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            role = result.scalar_one_or_none()
            if role is None:
                role = Role(**role_data)
                db.add(role)
                await db.flush()
            role_map[role.name] = role
        print(f"  {len(role_map)} roles ready.")

        # 3. Assign permissions to roles
        print("Assigning permissions to roles...")
        for role_name in FULL_ACCESS_ROLES:
            role = role_map[role_name]
            for perm in perm_map.values():
                existing = await db.execute(
                    select(role_permissions).where(
                        role_permissions.c.role_id == role.id,
                        role_permissions.c.permission_id == perm.id,
                    )
                )
                if existing.first() is None:
                    await db.execute(
                        role_permissions.insert().values(
                            role_id=role.id, permission_id=perm.id
                        )
                    )

        for role_name, perm_codenames in ROLE_PERMISSIONS.items():
            role = role_map[role_name]
            for codename in perm_codenames:
                perm = perm_map[codename]
                existing = await db.execute(
                    select(role_permissions).where(
                        role_permissions.c.role_id == role.id,
                        role_permissions.c.permission_id == perm.id,
                    )
                )
                if existing.first() is None:
                    await db.execute(
                        role_permissions.insert().values(
                            role_id=role.id, permission_id=perm.id
                        )
                    )
        print("  Permissions assigned.")

        # 4. Seed superadmin user
        print("Seeding superadmin user...")
        result = await db.execute(
            select(User).where(User.email == SUPERADMIN_EMAIL)
        )
        admin_user = result.scalar_one_or_none()
        if admin_user is None:
            admin_user = User(
                email=SUPERADMIN_EMAIL,
                password_hash=hash_password(SUPERADMIN_PASSWORD),
                first_name="Admin",
                last_name="Ganoherb",
                is_active=True,
                is_superadmin=True,
            )
            db.add(admin_user)
            await db.flush()
            # Assign super_admin role via join table (avoid lazy load in async)
            from app.models.associations import user_roles
            await db.execute(
                user_roles.insert().values(
                    user_id=admin_user.id,
                    role_id=role_map["super_admin"].id,
                )
            )
            print(f"  Superadmin created: {SUPERADMIN_EMAIL}")
        else:
            print(f"  Superadmin already exists: {SUPERADMIN_EMAIL}")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
