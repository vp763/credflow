# CredFlow System Architecture (C4 Level 1-2)

## Level 1: System Context

```mermaid
C4Context
    title System Context Diagram - CredFlow

    Person(sme, "Indian SME Owner/Accountant", "Uses CredFlow to manage receivables")
    Person(admin, "CredFlow Admin", "Manages platform, tenants, billing")

    System_Boundary(c1, "CredFlow Platform") {
        System(web, "Web Application", "Next.js 14 - Dashboard, Customers, Invoices, Collections, Payments, Settings")
        System(api, "API Backend", "FastAPI - REST API, Auth, Tally Sync, Business Logic")
        System(worker, "Background Workers", "Celery - Async jobs: Sync, Reminders, Payments, Analytics")
        System(scheduler, "Scheduler", "Celery Beat - Cron jobs: Aging, DSO, Reports")
        System(agent, "Tally Agent", "Go binary - Runs on customer Windows machine, extracts Tally data")
    }

    System_Ext(tally, "Tally ERP 9/Prime", "Local accounting software on customer premises")
    System_Ext(keycloak, "Keycloak / Azure Entra ID", "Identity Provider (OIDC/OAuth2)")
    System_Ext(whatsapp, "WhatsApp Provider", "Twilio / Gupshup / Wati Business API")
    System_Ext(email, "Email Provider", "SendGrid / AWS SES / SMTP")
    System_Ext(sms, "SMS Provider", "Twilio / MSG91")
    System_Ext(razorpay, "Razorpay", "Payment Gateway (Links, Webhooks)")
    System_Ext(azure, "Azure Cloud", "PostgreSQL, Redis, Blob Storage, Key Vault, Container Apps")

    Rel(sme, web, "Uses", "HTTPS")
    Rel(admin, web, "Administers", "HTTPS")
    Rel(web, api, "Calls", "REST/JSON")
    Rel(api, worker, "Enqueues jobs", "Redis Streams")
    Rel(scheduler, worker, "Triggers jobs", "Redis Streams")
    Rel(agent, tally, "Polls XML API", "HTTP/XML (localhost)")
    Rel(agent, api, "Uploads sync data", "HTTPS/JSON")
    Rel(api, keycloak, "Validates tokens", "OIDC")
    Rel(web, keycloak, "Auth flow", "OIDC")
    Rel(worker, whatsapp, "Sends reminders", "HTTPS")
    Rel(worker, email, "Sends reminders", "HTTPS/SMTP")
    Rel(worker, sms, "Sends reminders", "HTTPS")
    Rel(worker, razorpay, "Creates links, verifies webhooks", "HTTPS")
    Rel(api, azure, "Stores data", "PostgreSQL, Redis, Blob")
    Rel(worker, azure, "Stores data", "PostgreSQL, Redis, Blob")
```

## Level 2: Container Diagram

```mermaid
C4Container
    title Container Diagram - CredFlow Platform

    Container_Boundary(local, "Customer Premises (Windows)") {
        Container(tally_erp, "Tally ERP 9/Prime", "Windows App", "Local accounting software with HTTP XML API on port 9000")
        Container(tally_agent, "Tally Agent", "Go/Windows Service", "Polls Tally XML, queues locally (SQLite), uploads to cloud")
    }

    Container_Boundary(cloud, "Azure Cloud / Local Docker") {
        Container(nginx, "Nginx", "Reverse Proxy", "TLS termination, rate limiting, static file serving")
        Container(web, "Web App", "Next.js 14", "React dashboard, customer/invoice management, settings")
        Container(api, "API Backend", "FastAPI/Python", "REST API, auth, multi-tenant logic, Tally sync endpoint")
        Container(worker, "Worker", "Celery/Python", "Async job processing: tally, sync, notifications, payments, analytics")
        Container(scheduler, "Scheduler", "Celery Beat/Python", "Cron jobs: aging, DSO, reports, reminder engine")
        Container(redis, "Redis", "Redis 7", "Cache, Celery broker (Streams), session store")
        Container(postgres, "PostgreSQL", "PostgreSQL 16", "Primary data store with RLS, partitioning")
        Container(azurite, "Azurite / Azure Blob", "Blob Storage", "File storage: invoices, reports, exports")
        Container(keycloak, "Keycloak", "Identity Provider", "OIDC/OAuth2, user management, MFA")
    }

    Container_Ext(razorpay, "Razorpay", "Payment Gateway", "Payment links, webhooks")
    Container_Ext(whatsapp, "WhatsApp API", "Twilio/Gupshup", "WhatsApp Business API")
    Container_Ext(email, "Email API", "SendGrid/SES", "Transactional email")
    Container_Ext(sms, "SMS API", "Twilio/MSG91", "Transactional SMS")

    Rel(tally_agent, tally_erp, "Polls XML", "HTTP/XML (localhost:9000)")
    Rel(tally_agent, api, "Uploads sync", "HTTPS/JSON")
    Rel(web, nginx, "Serves via", "HTTP")
    Rel(web, api, "API calls", "HTTPS/REST")
    Rel(api, nginx, "Proxied via", "HTTP")
    Rel(worker, nginx, "Proxied via", "HTTP")
    Rel(api, redis, "Cache/Queue", "Redis Protocol")
    Rel(worker, redis, "Queue/Cache", "Redis Protocol")
    Rel(scheduler, redis, "Queue", "Redis Protocol")
    Rel(api, postgres, "Reads/Writes", "PostgreSQL Protocol")
    Rel(worker, postgres, "Reads/Writes", "PostgreSQL Protocol")
    Rel(api, azurite, "Blob storage", "S3/Blob API")
    Rel(worker, azurite, "Blob storage", "S3/Blob API")
    Rel(api, keycloak, "Token validation", "OIDC")
    Rel(web, keycloak, "Auth flow", "OIDC")
    Rel(worker, razorpay, "Payment ops", "HTTPS")
    Rel(worker, whatsapp, "Send msg", "HTTPS")
    Rel(worker, email, "Send email", "HTTPS/SMTP")
    Rel(worker, sms, "Send SMS", "HTTPS")
```

## Data Flow: Tally Sync

```mermaid
sequenceDiagram
    participant Agent as Tally Agent (Go)
    participant Tally as Tally ERP (Local)
    participant API as CredFlow API
    participant Worker as Celery Worker
    participant DB as PostgreSQL
    participant Redis as Redis Streams

    Agent->>Tally: POST / HTTP/XML (Company List)
    Tally-->>Agent: XML Response (Companies)
    Agent->>Tally: POST / HTTP/XML (Ledgers/Customers)
    Tally-->>Agent: XML Response (Customers)
    Agent->>Tally: POST / HTTP/XML (Sales Vouchers)
    Tally-->>Agent: XML Response (Invoices)
    Agent->>Tally: POST / HTTP/XML (Receipt Vouchers)
    Tally-->>Agent: XML Response (Payments)

    Agent->>Agent: Transform XML → JSON payload
    Agent->>Agent: Store in local SQLite queue (durability)
    
    loop For each batch
        Agent->>API: POST /api/v1/tally/sync (JSON)
        API->>Redis: Enqueue process_tally_sync job
        API-->>Agent: 202 Accepted
        
        Worker->>Redis: Reserve job
        Worker->>API: Process sync (parse, validate, upsert)
        Worker->>DB: Upsert customers, invoices, payments
        Worker->>DB: Create sync_log record
        Worker->>Redis: Mark job complete
    end
```

## Data Flow: Reminder Engine

```mermaid
sequenceDiagram
    participant Scheduler as Celery Beat
    participant Worker as Celery Worker
    participant DB as PostgreSQL
    participant WhatsApp as WhatsApp API
    participant Email as Email API

    Scheduler->>Worker: Trigger reminder_engine (hourly)
    Worker->>DB: Find invoices due/overdue per tenant
    Worker->>DB: Check reminder rules (templates, schedule)
    Worker->>DB: Deduplicate (invoice + channel + date)
    Worker->>DB: Skip if paid/disputed/opted-out/promised
    
    loop For each reminder to send
        Worker->>DB: Create communication record (pending)
        Worker->>WhatsApp: Send template message
        alt WhatsApp success
            Worker->>DB: Update communication (sent, provider_id)
        else WhatsApp fails
            Worker->>Email: Fallback to email
            Worker->>DB: Update communication (sent/failed)
        end
    end
```

## Infrastructure: Local ↔ Azure Parity

| Component | Local (Docker Compose) | Azure Production |
|-----------|------------------------|------------------|
| **API** | `backend` container | Azure Container Apps |
| **Worker** | `worker` container | Azure Container Apps (scale: 0-10) |
| **Scheduler** | `scheduler` container | Azure Container Apps (single replica) |
| **Frontend** | `frontend` container | Azure Static Web Apps / Container Apps |
| **Nginx** | `nginx` container | Azure Front Door / App Gateway |
| **PostgreSQL** | `postgres:16` | Azure PostgreSQL Flexible Server |
| **Redis** | `redis:7-alpine` | Azure Cache for Redis (Premium) |
| **Blob Storage** | `azurite` | Azure Blob Storage |
| **Key Vault** | `.env` + mock endpoint | Azure Key Vault |
| **Identity** | `keycloak` | Azure Entra ID |
| **Monitoring** | Loki + Grafana + Tempo | Azure Monitor + App Insights |
| **CI/CD** | GitHub Actions | GitHub Actions → Azure |

## Network Architecture (Azure)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure VNet                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Public Subnet  │  │  Private Subnet │  │  Data Subnet    │  │
│  │                 │  │                 │  │                 │  │
│  │ • Front Door    │  │ • Container Apps│  │ • PostgreSQL    │  │
│  │ • App Gateway   │  │   (API, Worker, │  │ • Redis Cache   │  │
│  │ • Static Web App│  │    Scheduler)   │  │ • Blob Storage  │  │
│  │                 │  │ • Key Vault     │  │                 │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                ▼                                │
│                     ┌─────────────────────┐                     │
│                     │   Private DNS Zones │                     │
│                     │   Service Endpoints │                     │
│                     └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Security Boundaries

1. **Internet → Front Door/WAF** → DDoS protection, rate limiting, geo-filtering
2. **Front Door → App Gateway** → TLS termination, path-based routing
3. **App Gateway → Container Apps** → Private networking, no public IPs
4. **Container Apps → PostgreSQL/Redis/Blob** → Private endpoints, service endpoints
5. **Key Vault** → Accessed via Managed Identity, no secrets in code
6. **Tally Agent → API** → mTLS or API Key + HTTPS, domain allowlist