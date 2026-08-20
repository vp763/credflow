# CredFlow Security Model

## Overview
Multi-layer defense-in-depth security architecture for multi-tenant SaaS handling financial data.

## 1. AUTHENTICATION

### 1.1 Identity Providers
| Environment | Provider | Purpose |
|-------------|----------|---------|
| Local Dev | Keycloak | OIDC/OAuth2, mimics Azure Entra ID |
| Staging | Azure Entra ID (test tenant) | Pre-prod validation |
| Production | Azure Entra ID | Enterprise SSO, MFA, Conditional Access |

### 1.2 Token Structure

#### Access Token (JWT, 15 min)
```json
{
  "sub": "user_uuid",
  "tenant_id": "tenant_uuid",
  "email": "user@company.com",
  "role": "tenant_admin",
  "permissions": ["invoices:read", "invoices:write", "customers:read", ...],
  "exp": 1705312200,
  "iat": 1705311300,
  "jti": "unique_token_id",
  "type": "access"
}
```

#### Refresh Token (JWT, 7 days, HttpOnly Cookie)
```json
{
  "sub": "user_uuid",
  "tenant_id": "tenant_uuid",
  "exp": 1705896000,
  "iat": 1705311300,
  "jti": "unique_token_id",
  "type": "refresh"
}
```

#### Agent API Key
- Format: `cf_{32_bytes_urlsafe}` (e.g., `cf_abc123def456...`)
- Storage: SHA256 hash in database
- Header: `X-Agent-Key: cf_abc123...`
- Rotation: Manual via UI, old key revoked immediately

### 1.3 Token Lifecycle
```
Login → Keycloak/Azure → Auth Code → Token Endpoint → Access + Refresh Tokens
                              ↓
                     Access Token (15 min, memory only)
                     Refresh Token (7 days, HttpOnly Secure Cookie)
                              ↓
                     API Requests → Authorization: Bearer <access>
                              ↓
                     401 + TOKEN_EXPIRED → POST /auth/refresh (cookie)
                              ↓
                     New Access + Refresh (rotation)
                              ↓
                     Logout → Revoke Refresh Token (DB) + Clear Cookie
```

### 1.4 Password Policy
- Min 12 characters
- Require: uppercase, lowercase, number, special char
- Bcrypt cost factor: 12
- Breach check: HaveIBeenPwned API (on registration/password change)

---

## 2. AUTHORIZATION (RBAC)

### 2.1 Roles
| Role | Description | Scope |
|------|-------------|-------|
| `super_admin` | Platform operator | All tenants, all resources |
| `tenant_admin` | Tenant owner/admin | All resources within tenant |
| `analyst` | Finance team member | Read/write invoices, customers, collections |
| `viewer` | Read-only access | Read-only all tenant data |
| `agent` | Tally Agent (machine) | Sync endpoint only |

### 2.2 Permission Matrix

| Permission | super_admin | tenant_admin | analyst | viewer | agent |
|------------|-------------|--------------|---------|--------|-------|
| **Tenants** | | | | | |
| tenants:create | ✅ | ❌ | ❌ | ❌ | ❌ |
| tenants:read | ✅ | ✅ (own) | ❌ | ❌ | ❌ |
| tenants:update | ✅ | ✅ (own) | ❌ | ❌ | ❌ |
| tenants:delete | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Users** | | | | | |
| users:invite | ✅ | ✅ | ❌ | ❌ | ❌ |
| users:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| users:update_role | ✅ | ✅ | ❌ | ❌ | ❌ |
| users:remove | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Agents** | | | | | |
| agents:register | ✅ | ✅ | ❌ | ❌ | ❌ |
| agents:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| agents:heartbeat | ❌ | ❌ | ❌ | ❌ | ✅ |
| agents:delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Customers** | | | | | |
| customers:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| customers:write | ✅ | ✅ | ✅ | ❌ | ❌ (sync only) |
| **Invoices** | | | | | |
| invoices:read | ✅ | ✅ | ✅ | ✅ | ❌ (sync only) |
| invoices:write | ✅ | ✅ | ✅ | ❌ | ❌ (sync only) |
| invoices:delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Payments** | | | | | |
| payments:read | ✅ | ✅ | ✅ | ✅ | ❌ (sync only) |
| payments:write | ✅ | ✅ | ✅ | ❌ | ❌ (sync only) |
| payments:webhook | ❌ | ❌ | ❌ | ❌ | ❌ (public endpoint) |
| **Collections** | | | | | |
| templates:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| templates:write | ✅ | ✅ | ✅ | ❌ | ❌ |
| reminders:send | ✅ | ✅ | ✅ | ❌ | ❌ |
| tasks:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| tasks:write | ✅ | ✅ | ✅ | ❌ | ❌ |
| disputes:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| disputes:write | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Analytics** | | | | | |
| dashboard:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| reports:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Settings** | | | | | |
| settings:read | ✅ | ✅ | ✅ | ✅ | ❌ |
| settings:write | ✅ | ✅ | ❌ | ❌ | ❌ |
| billing:read | ✅ | ✅ | ❌ | ❌ | ❌ |

### 2.3 Implementation
```python
# FastAPI dependency
def require_permission(permission: str):
    def checker(current_user: User = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise ForbiddenError(f"Missing permission: {permission}")
        return current_user
    return checker

# Usage
@router.post("/invoices", dependencies=[Depends(require_permission("invoices:write"))])
async def create_invoice(...):
    ...
```

---

## 3. TENANT ISOLATION (4 Layers)

### Layer 1: JWT Token
- `tenant_id` claim in signed JWT
- Tamper-proof (RS256 signature)
- Validated on every request

### Layer 2: FastAPI Middleware
```python
class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        # 1. Validate JWT
        payload = decode_token(request.headers.get("Authorization"))
        # 2. Extract tenant_id
        tenant_id = payload["tenant_id"]
        # 3. Verify tenant exists & active
        tenant = await db.get_tenant(tenant_id)
        if not tenant or tenant.status != "active":
            raise ForbiddenError("Tenant suspended")
        # 4. Set request state
        request.state.tenant_id = tenant_id
        request.state.user_id = payload["sub"]
        request.state.role = payload["role"]
        request.state.permissions = payload["permissions"]
        return await call_next(request)
```

### Layer 3: SQLAlchemy ORM Auto-Filter
```python
# Base model mixin
class TenantMixin:
    @declared_attr
    def tenant_id(cls):
        return Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)

# Query mixin
class TenantQueryMixin:
    @classmethod
    def query_for_tenant(cls, session: AsyncSession, tenant_id: UUID):
        return session.query(cls).filter(cls.tenant_id == tenant_id)

# Event listener: auto-set tenant_id on INSERT
@event.listens_for(Base, "before_insert", propagate=True)
def set_tenant_id(mapper, connection, target):
    if hasattr(target, "tenant_id") and not target.tenant_id:
        target.tenant_id = get_current_tenant_id()  # From context var
```

### Layer 4: PostgreSQL Row-Level Security
```sql
-- Enable RLS
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Policy
CREATE POLICY tenant_isolation ON invoices FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);

-- Middleware sets context per transaction
SET LOCAL app.tenant_id = 'tenant-uuid-here';
```

### RLS Policy Template (Applied to All Tenant Tables)
```sql
CREATE POLICY tenant_isolation ON {table} FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);

-- Tables: users, agents, tally_companies, sync_logs, customers, invoices,
-- payments, reminder_templates, communications, payment_links,
-- collection_tasks, disputes, audit_logs, notification_providers,
-- dashboard_snapshots, customer_risk_scores
```

### Super Admin Bypass
```sql
CREATE ROLE super_admin WITH BYPASSRLS;
-- Only used by platform operators via secure bastion
```

---

## 4. DATA SECURITY

### 4.1 PII Inventory
| Table | PII Fields | Protection |
|-------|------------|------------|
| `users` | email, name | Encrypted at rest (TDE), hashed in logs |
| `customers` | name, gstin, address, contact_person, phone, email | Encrypted at rest, masked in logs |
| `invoices` | gstin, place_of_supply | Encrypted at rest |
| `communications` | recipient, body | Encrypted at rest |
| `audit_logs` | ip_address, user_agent | Hashed in logs |

### 4.2 Encryption
| Data | Algorithm | Key Management |
|------|-----------|----------------|
| Database at rest | AES-256 (TDE) | Azure Managed Keys / Customer Keys |
| Secrets (API keys, provider configs) | AES-256-GCM | Azure Key Vault / Local libsodium |
| Passwords | Bcrypt (cost=12) | N/A (hashed) |
| Refresh tokens | SHA256 hash | N/A (hashed) |
| Agent API keys | SHA256 hash | N/A (hashed) |
| TLS in transit | TLS 1.3 | Azure Front Door / App Gateway |

### 4.3 Logging Rules
```python
# Structured logging with automatic PII masking
LOG_MASK_PATTERNS = [
    r'"email":\s*"[^"]*"',           # "email": "user@domain.com"
    r'"phone":\s*"[^"]*"',           # "phone": "9876543210"
    r'"gstin":\s*"[^"]*"',           # "gstin": "27AAACR5055K1ZP"
    r'"address":\s*\{[^}]*\}',       # "address": {...}
    r'Bearer\s+[A-Za-z0-9\-_.]+',    # Authorization: Bearer <token>
    r'X-Agent-Key:\s*cf_[A-Za-z0-9_-]+',  # Agent key
]

# Never log:
# - Full credit card numbers
# - Passwords (even hashed)
# - API secrets
# - Refresh tokens
# - Razorpay webhook secrets
```

### 4.4 Log Retention
| Log Type | Retention | Storage |
|----------|-----------|---------|
| Application logs | 30 days | Loki (local) / Azure Monitor |
| Audit logs | 7 years | PostgreSQL (partitioned) |
| Access logs (Nginx) | 90 days | Azure Blob / Loki |
| Security events | 1 year | Dedicated SIEM |

---

## 5. API SECURITY

### 5.1 CORS Policy
```python
CORS_ORIGINS = [
    "https://app.credflow.in",
    "https://staging.credflow.in",
    "http://localhost:3000",  # dev only
]

# Headers
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type", "X-Agent-Key", "X-Request-ID"]
CORS_EXPOSE_HEADERS = ["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
```

### 5.2 Security Headers (Nginx)
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.credflow.in https://*.razorpay.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### 5.3 Rate Limiting
```python
# Per-tenant, per-endpoint limits
RATE_LIMITS = {
    "auth": "10/minute",
    "agents": "30/minute",
    "tally_sync": "5/minute",  # agent
    "customers": "100/minute",
    "invoices": "100/minute",
    "collections": "50/minute",
    "payments": "30/minute",
    "dashboard": "60/minute",
    "settings": "20/minute",
    "public_payment": "20/minute per IP",
}

# Implementation: Redis sliding window
# Key: "ratelimit:{tenant_id}:{endpoint}:{window}"
```

### 5.4 Webhook Security

#### Razorpay
```python
async def verify_razorpay_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# Idempotency: UNIQUE constraint on razorpay_payment_id
```

#### WhatsApp/Email/SMS Providers
- Validate provider-specific signature headers
- Process async via Celery (not in webhook handler)
- Store provider_message_id for deduplication

---

## 6. BRUTE FORCE PROTECTION

### 6.1 Login Attempts
```python
# Redis tracking
LOGIN_ATTEMPTS_KEY = "login_attempts:{ip}:{email}"

MAX_ATTEMPTS = 5
LOCKOUT_DURATION = 15 * 60  # 15 minutes

async def check_brute_force(ip: str, email: str) -> bool:
    key = f"login_attempts:{ip}:{email}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, LOCKOUT_DURATION)
    return attempts > MAX_ATTEMPTS
```

### 6.2 Account Lockout
- 5 failed attempts → 15 min lockout
- 20 failed attempts in 24h → 1 hour lockout + admin alert
- Notify user on lockout (email)

### 6.3 IP Rate Limiting
- Global: 100 req/min per IP
- Auth endpoints: 10 req/min per IP
- Public payment: 20 req/min per IP

---

## 7. SECRETS MANAGEMENT

### 7.1 Local Development
```
.env.local (gitignored)
├── DATABASE_URL
├── REDIS_URL
├── JWT_SECRET_KEY
├── KEYCLOAK_CLIENT_SECRET
├── RAZORPAY_KEY_SECRET
├── WHATSAPP_AUTH_TOKEN
├── SENDGRID_API_KEY
└── TWILIO_AUTH_TOKEN
```

### 7.2 Production (Azure Key Vault)
| Secret Name | Description | Rotation |
|-------------|-------------|----------|
| `db-password` | PostgreSQL password | 90 days |
| `redis-password` | Redis access key | 90 days |
| `jwt-secret` | JWT signing key | 90 days |
| `keycloak-client-secret` | OIDC client secret | 180 days |
| `razorpay-key-secret` | Razorpay secret | 90 days |
| `whatsapp-auth-token` | WhatsApp provider token | Per provider |
| `sendgrid-api-key` | SendGrid API key | 90 days |
| `twilio-auth-token` | Twilio auth token | 90 days |

### 7.3 Access Control
- **Managed Identity**: Each Container App has system-assigned MI
- **Key Vault Access Policy**: MI gets `get`/`list` on secrets
- **No secrets in code**: All via environment variables at runtime
- **Secret injection**: Azure Container Apps injects from Key Vault

---

## 8. COMPLIANCE & AUDIT

### 8.1 Audit Logging
```python
# Automatic via middleware + event listeners
async def log_audit(
    action: str,
    entity_type: str,
    entity_id: UUID,
    old_values: dict = None,
    new_values: dict = None
):
    await db.execute(
        insert(AuditLog).values(
            tenant_id=current_tenant_id(),
            user_id=current_user_id(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent")
        )
    )
```

### 8.2 Audited Actions
| Category | Actions |
|----------|---------|
| Auth | login, logout, password_change, mfa_enabled, token_refresh |
| Tenant | create, update, suspend, activate, delete |
| User | invite, join, role_change, remove, deactivate |
| Agent | register, heartbeat, update, delete |
| Data | create, update, delete (invoices, customers, payments, etc.) |
| Settings | update (tally, reminders, payments, notifications) |
| Export | download_report, export_data |

### 8.3 Data Retention
| Data Type | Retention | Disposal |
|-----------|-----------|----------|
| Customer/Invoice/Payment data | 7 years (legal) | Anonymize after |
| Audit logs | 7 years | Archive to cold storage |
| Communications | 3 years | Delete |
| Sync logs | 2 years | Aggregate + delete |
| Session/token data | 30 days | Auto-expire |

---

## 9. INCIDENT RESPONSE

### 9.1 Security Event Classification
| Severity | Examples | Response Time |
|----------|----------|---------------|
| **Critical** | Data breach, RLS bypass, SQL injection | 1 hour |
| **High** | Auth bypass, privilege escalation, mass data access | 4 hours |
| **Medium** | Rate limit abuse, suspicious login patterns | 24 hours |
| **Low** | Failed login attempts, config drift | 72 hours |

### 9.2 Response Playbook
1. **Detect**: Alert from monitoring (WAF, RLS violations, anomalous queries)
2. **Contain**: Revoke tokens, disable agents, block IPs, enable maintenance mode
3. **Investigate**: Query audit logs, analyze access patterns
4. **Remediate**: Patch vulnerability, rotate secrets, restore data
5. **Notify**: Affected tenants, regulators (if PII breach), stakeholders
6. **Post-mortem**: Root cause, timeline, preventive measures

---

## 10. SECURITY CHECKLIST (Per Release)

- [ ] All new endpoints have RBAC checks
- [ ] New tables have RLS policies
- [ ] PII fields identified and masked in logs
- [ ] Secrets in Key Vault, not in code/config
- [ ] Rate limits configured for new endpoints
- [ ] Webhook signatures verified
- [ ] CORS origins reviewed
- [ ] Security headers present
- [ ] Dependency scan (Snyk/GitHub Dependabot) clean
- [ ] SAST scan (Bandit/Semgrep) clean
- [ ] Penetration test scheduled (quarterly)