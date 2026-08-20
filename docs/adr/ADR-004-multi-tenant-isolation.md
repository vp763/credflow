# ADR-004: Multi-Tenant Isolation - 4-Layer Defense

## Context
CredFlow is a multi-tenant SaaS serving Indian SMEs. Tenant data isolation is critical:
- 100→10,000 tenants
- Financial data (invoices, payments, customer info)
- Regulatory compliance (GST, financial records)
- Zero tolerance for cross-tenant data leaks

## Decision
Implement **4-layer tenant isolation** (defense in depth):

### Layer 1: JWT Token (Client → API)
- Access token contains `tenant_id` claim (signed, tamper-proof)
- Token validated on every request
- Short-lived (15 min), rotated via refresh token

### Layer 2: FastAPI Middleware (Request → Context)
```python
# Middleware extracts tenant_id from validated JWT
# Sets request.state.tenant_id for downstream use
# Rejects requests without valid tenant context
```
- Validates JWT signature and expiration
- Extracts `tenant_id`, `user_id`, `role`, `permissions`
- Sets `request.state.tenant_id` for ORM layer

### Layer 3: SQLAlchemy ORM (Query → Auto-filter)
```python
# Base query mixin automatically adds tenant filter
class TenantMixin:
    @declared_attr
    def tenant_id(cls):
        return Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)

    @classmethod
    def query_for_tenant(cls, session, tenant_id):
        return session.query(cls).filter(cls.tenant_id == tenant_id)
```
- All model queries automatically filtered by `tenant_id`
- Session-scoped tenant context via event listeners
- Impossible to query without tenant context (enforced at base class)

### Layer 4: PostgreSQL RLS (Database → Enforcement)
```sql
-- Enable RLS on all tenant tables
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Policy uses session variable set by middleware
CREATE POLICY tenant_isolation ON invoices
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Session variable set per connection
SET LOCAL app.tenant_id = 'tenant-uuid-here';
```
- Database-enforced isolation (cannot be bypassed by code bugs)
- Works even with raw SQL, direct DB access, admin tools
- Policy applied at row level for SELECT, INSERT, UPDATE, DELETE

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Schema-per-tenant** | Physical isolation, simple queries | Operational nightmare at 10k tenants (migrations, connections, backups) |
| **Single schema + tenant_id column (app-level only)** | Simple | One bug = total data leak; no defense in depth |
| **4-layer (JWT → Middleware → ORM → RLS)** | Defense in depth, DB-enforced, audit-compliant | More initial setup, slight latency |

## Consequences

**Positive:**
- **Zero-trust**: Even if one layer fails, others protect data
- **Compliance-ready**: Database-enforced isolation meets audit requirements
- **Developer-friendly**: ORM auto-filters mean developers can't forget tenant checks
- **Testable**: Each layer can be unit/integration tested independently
- **Scalable**: Shared schema scales to 100k+ tenants with partitioning

**Negative:**
- More moving parts to configure initially
- RLS requires `SET LOCAL` per transaction (middleware handles this)
- Debugging requires tenant context in DB sessions

## Implementation Notes
- Middleware sets `app.tenant_id` via `SET LOCAL` on connection checkout
- Connection pool event listeners reset tenant context on checkin
- All tenant tables have `tenant_id` NOT NULL + FK to `tenants`
- RLS policies created via Alembic migration
- Tests verify: Tenant A cannot read Tenant B data at all 4 layers
- Super admin bypass via separate role with `BYPASSRLS` (audited)