# CLAUDE.md — Instrucciones para Claude Code

## Comunicacion

- **Siempre dar contexto antes de cada cambio**: explicar *que* se va a hacer y *por que* antes de escribir/editar un archivo. No hacer cambios silenciosos.
- Hablar en espanol salvo que el usuario cambie de idioma.
- Codigo y nombres de variables/funciones siempre en ingles.

## Documentacion

- **Todo el contexto, decisiones e historial de progreso debe quedar en archivos versionados en Git**, no en memorias locales de herramientas. El equipo trabaja desde multiples maquinas.
- **Al finalizar cada sesion**, actualizar `context.md` con los cambios realizados y comitear.
- Fuente de verdad: `context.md` (tecnico + bitacora), `schema.md` (BD), `flujos.md` (flujos operativos), `modulos.md` (funcional), `plan.md` (negocio).

## Proyecto

- **Back Office MLM Ganoherb** — sistema de gestion para empresa de venta directa (MLM binario hibrido progresivo).
- Documentacion de negocio: `back_office_portal/plan.md`, `back_office_api/modulos.md`
- Documentacion tecnica: `back_office_api/context.md`, `back_office_api/schema.md`
- Stack: FastAPI + SQLAlchemy 2.0 async + PostgreSQL 17 (Neon) + Alembic
- Pais inicial: El Salvador (expansion futura multi-pais/multi-tenant)
