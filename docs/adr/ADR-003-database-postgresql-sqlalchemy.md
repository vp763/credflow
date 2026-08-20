# ADR-003: Database & ORM - PostgreSQL + SQLAlchemy 2.0 + Alembic

## Context
CredFlow requires a relational database with:
- Multi-tenant data isolation at scale (100→10,000 tenants)
- Complex queries for aging analysis, DSO, cash flow forecasting
- ACID transactions for payment reconciliation
- Soft deletes, audit logs, partitioning for large tables
- Row-Level Security (RLS) for tenant isolation
- Type-safe ORM with async support
- Migration management

## Decision
Use **PostgreSQL 16** with **SQLAlchemy 2.0 (async)** and **Alembic** for migrations.

### Core Stack
- **Database**: PostgreSQL 16 (production), SQLite (local dev - optional)
- **ORM**: SQLAlchemy 2.0 with asyncpg driver
- **Migrations**: Alembic with async support
- **Connection Pool**: asyncpg pool (10-20 connections per worker)
- **RLS**: PostgreSQL Row-Level Security policies on all tenant tables

### Table Standards (All Tenant Tables)
```sql
-- Required columns on every tenant-scoped table
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id       UUID NOT NULL REFERENCES tenants(id)
created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at      TIMESTAMPTZ  -- soft delete
```

### Partitioning Strategy
| Table | Partition By | Rationale |
|-------|--------------|-----------|
| `invoices` | `tenant_id` + `date_trunc('month', due_date)` | High volume, time-range queries |
| `communications` | `date_trunc('month', created_at)` | Append-only, time-range queries |
| `audit_logs` | `date_trunc('month', created_at)` | Append-only, retention policies |
| `sync_logs` | `date_trunc('month', created_at)` | Append-only, debugging |

### Indexing Strategy
- Composite indexes matching query patterns (tenant_id + status + due_date)
- Partial indexes for common filters (e.g., `WHERE status = 'open'`)
- BRIN indexes on timestamp columns for partitioned tables

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Prisma** | Great DX, type-safe, visual schema | Limited RLS support, no native partitioning, slower for complex queries |
| **Drizzle ORM** | Lightweight, fast, SQL-like | Newer, smaller ecosystem, less mature migration tooling |
| **SQLAlchemy 2.0** | Mature, full async, RLS support, partitioning, powerful query builder | More verbose, steeper learning curve |
| **Raw SQL / pgx** | Maximum control, performance | No type safety, manual migration management |

## Consequences

**Positive:**
- Full RLS support for tenant isolation at database level
- Native partitioning for large tables (invoices, communications)
- Powerful async query builder with type safety
- Alembic for version-controlled migrations
- Mature ecosystem, battle-tested at scale
- Works seamlessly with FastAPI async

**Negative:**
- More verbose than Prisma/Drizzle for simple CRUD
- Migration files require manual review
- Need to understand SQLAlchemy's async patterns

## Implementation Notes
- All models inherit from `Base` with `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`
- Tenant context set via `SET LOCAL app.tenant_id = '...'` in middleware
- RLS policies: `CREATE POLICY tenant_isolation ON table FOR ALL USING (tenant_id = current_setting('app.tenant_id')::uuid)`
- Soft delete: `deleted_at IS NULL` filter in all queries (via base query mixin)
- Partition maintenance: pg_partman or custom cron for partition creation/detachment
- Alembic env configured for async with `run_migrations_online` using asyncpg