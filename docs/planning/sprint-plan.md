# CredFlow Sprint Plan (12 Weeks / 6 Sprints)

## Sprint Overview

| Sprint | Duration | Theme | Goal |
|--------|----------|-------|------|
| **Sprint 1** | Week 1-2 | **Foundation** | Repo, CI/CD, Auth, DB, Deploy pipeline |
| **Sprint 2** | Week 3-4 | **Tally Sync** | Agent → Cloud → DB → API |
| **Sprint 3** | Week 5-6 | **Core Data** | Customers, Invoices, Aging API |
| **Sprint 4** | Week 7-8 | **Reminders** | WhatsApp/Email + Scheduler |
| **Sprint 5** | Week 9-10 | **Payments** | Razorpay Links + Webhook |
| **Sprint 6** | Week 11-12 | **Dashboard + Launch** | KPIs, Polish, Production Ready |

---

## Sprint 1: Foundation (Week 1-2)
**Goal**: Auth working + team can log in + CI/CD deploying

### DevOps (Lead)
- [ ] **DV-001** Initialize GitHub repo with branch protection, PR template
- [ ] **DV-002** Create `docker-compose.yml` with all 8 services (PostgreSQL, Redis, Azurite, Keycloak, Backend, Worker, Scheduler, Frontend, Nginx, Mock-Tally)
- [ ] **DV-003** GitHub Actions: `lint → typecheck → test → build → push` pipeline
- [ ] **DV-004** Configure Keycloak realm: `credflow` with client `credflow-backend`, `credflow-frontend`
- [ ] **DV-005** Staging environment: Azure Container Apps (or Railway/Fly.io for MVP)
- [ ] **DV-006** Secrets management: GitHub Environments + Azure Key Vault (staging)
- [ ] **DV-007** Monitoring: Loki + Grafana + Tempo (local), Azure Monitor (staging)
- [ ] **DV-008** Runbooks: Deploy, rollback, DB migration, incident response

### Backend (Lead)
- [ ] **BE-001** FastAPI skeleton: config, database, security, main.py
- [ ] **BE-002** SQLAlchemy models: Tenant, User, Invitation, RefreshToken, Agent
- [ ] **BE-003** Alembic migrations: initial schema with RLS policies
- [ ] **BE-004** Auth endpoints: `/register`, `/login`, `/callback`, `/refresh`, `/logout`, `/me`
- [ ] **BE-005** JWT + Keycloak integration (OIDC flow)
- [ ] **BE-006** TenantMiddleware + RLS context setting
- [ ] **BE-007** Agent endpoints: `/register`, `/heartbeat`, `/list`
- [ ] **BE-008** Health check: `/health` with DB/Redis/Keycloak checks
- [ ] **BE-009** Unit tests: auth flow, tenant isolation, token refresh
- [ ] **BE-010** OpenAPI spec generation (auto from FastAPI)

### Frontend (Support)
- [ ] **FE-001** Next.js 14 + TypeScript + Tailwind + shadcn/ui init
- [ ] **FE-002** TanStack Query provider + API client (generated from OpenAPI)
- [ ] **FE-003** Keycloak OIDC login flow: Login → Callback → Protected routes
- [ ] **FE-004** Layout: Sidebar, Header, Tenant switcher (super_admin only)
- [ ] **FE-005** Login page + Protected route wrapper
- [ ] **FE-006** Dashboard shell (empty KPI cards)

### Database Optimizer (Review)
- [ ] **DB-001** Review ER diagram, indexes, partitioning strategy
- [ ] **DB-002** Review RLS policies on all tables
- [ ] **DB-003** Migration review: naming, rollback safety

### Definition of Done (Sprint 1)
- [ ] `docker compose up` → all 8 services healthy
- [ ] `npm run lint/typecheck/test` pass in CI
- [ ] Register tenant → login → see dashboard shell
- [ ] Staging deployed and accessible
- [ ] All ADRs approved

---

## Sprint 2: Tally Sync (Week 3-4)
**Goal**: Tally data visible on dashboard (mock → real)

### Backend (Lead)
- [ ] **BE-011** Tally XML parsers: Company, Ledgers, Sales Vouchers, Receipt Vouchers
- [ ] **BE-012** Mock Tally server (Flask) serving sample XML
- [ ] **BE-013** Sync endpoint: `POST /api/v1/tally/sync` (accepts JSON payload)
- [ ] **BE-013** Celery task: `process_tally_sync` (upsert customers, invoices, payments)
- [ ] **BE-014** Sync log model + endpoint: `GET /api/v1/tally/sync-logs`
- [ ] **BE-015** Company endpoints: `GET /api/v1/tally/companies`
- [ ] **BE-016** Delta sync logic: track `last_synced_at` per company/entity
- [ ] **BE-017** Field mapping validation + error handling
- [ ] **BE-018** Integration tests: full sync flow (mock → API → DB)

### Frontend (Lead)
- [ ] **FE-007** Settings → Tally: Agent registration, company linking
- [ ] **FE-008** Sync status page: Last sync, record counts, error display
- [ ] **FE-009** Manual sync trigger button
- [ ] **FE-010** Company selector (if multiple)

### Database Optimizer (Lead)
- [ ] **DB-004** Models + migrations: TallyCompany, SyncLog
- [ ] **DB-005** Indexes: sync_logs (tenant, started_at), customers (tally_ledger_guid)
- [ ] **DB-006** Partitioning: sync_logs by month

### DevOps (Support)
- [ ] **DV-009** Worker/Scheduler containers in docker-compose
- [ ] **DV-010** Celery Flower monitoring (dev)
- [ ] **DV-011** Staging: Tally agent test (Windows VM)

### Definition of Done (Sprint 2)
- [ ] Mock Tally → Agent → Cloud sync works end-to-end
- [ ] 6 customers, 6 invoices, 7 payments visible in DB
- [ ] Sync logs show success/failure with details
- [ ] Frontend shows sync status

---

## Sprint 3: Core Data (Week 5-6)
**Goal**: Customer/Invoice CRUD + Aging API working

### Backend (Lead)
- [ ] **BE-019** Customer CRUD + filtering/search
- [ ] **BE-020** Invoice CRUD + filtering
- [ ] **BE-021** Payment CRUD
- [ ] **BE-022** Aging calculation: 6 buckets (CURRENT, D1_30, D31_60, D61_90, D91_180, D180_PLUS)
- [ ] **BE-023** Aging endpoint: `GET /api/v1/invoices/aging`
- [ ] **BE-024** Overdue endpoint: `GET /api/v1/invoices/overdue`
- [ ] **BE-025** Customer detail: timeline (invoices, payments, communications)
- [ ] **BE-026** Pagination (cursor + offset) on all list endpoints
- [ ] **BE-027** Performance: composite indexes, query optimization

### Frontend (Lead)
- [ ] **FE-011** Customer list: table, search, filters (status, risk, outstanding)
- [ ] **FE-012** Customer detail: info, invoices tab, payments tab, timeline tab
- [ ] **FE-013** Invoice list: table, filters (status, aging, date range)
- [ ] **FE-014** Invoice detail: info, payments, communication history
- [ ] **FE-015** Aging page: bucket summary cards + detailed table
- [ ] **FE-016** Overdue page: actionable list with quick actions

### Database Optimizer (Lead)
- [ ] **DB-007** Models + migrations: Customer, Invoice, Payment
- [ ] **DB-008** Indexes: invoices (tenant, status, due_date), (customer, status)
- [ ] **DB-009** Partitioning: invoices by tenant + month
- [ ] **DB-010** Views: `v_invoice_aging`, `v_customer_outstanding`
- [ ] **DB-011** Aging recalculation job (hourly)

### DevOps (Support)
- [ ] **DV-012** Load test: 10k invoices sync, aging query < 500ms

### Definition of Done (Sprint 3)
- [ ] Customer/Invoice CRUD working with filters
- [ ] Aging API returns correct bucket amounts
- [ ] Dashboard shows real data from DB
- [ ] Performance: aging query < 200ms for 10k invoices

---

## Sprint 4: Reminders (Week 7-8)
**Goal**: Automated WhatsApp/Email reminders sending

### Backend (Lead)
- [ ] **BE-028** ReminderTemplate CRUD
- [ ] **BE-029** Reminder engine: deduplication, skip rules (paid, disputed, opt-out, promised)
- [ ] **BE-030** Template variables: `{{customer_name}}`, `{{invoice_number}}`, `{{amount}}`, `{{due_date}}`, `{{days_overdue}}`, `{{payment_link}}`
- [ ] **BE-031** WhatsApp provider integration (Twilio/Gupshup)
- [ ] **BE-032** Email provider integration (SendGrid)
- [ ] **BE-033** Communication log model + endpoints
- [ ] **BE-034** Celery tasks: `send_whatsapp`, `send_email`, `send_sms`
- [ ] **BE-035** Celery Beat schedule: hourly reminder engine
- [ ] **BE-036** Collection tasks: CRUD, assignment
- [ ] **BE-037** Disputes: CRUD, pause reminders

### Frontend (Lead)
- [ ] **FE-017** Templates page: list, create, edit, delete, preview
- [ ] **FE-018** Communications history: filter by channel, status, date
- [ ] **FE-019** Collection tasks: Kanban board (todo/in-progress/done)
- [ ] **FE-020** Disputes page: list, detail, resolve
- [ ] **FE-021** Manual reminder send: select invoices + template

### Database Optimizer (Lead)
- [ ] **DB-012** Models + migrations: ReminderTemplate, Communication, CollectionTask, Dispute
- [ ] **DB-013** Unique index: communications dedup (tenant, invoice, channel, date)
- [ ] **DB-014** Partitioning: communications by month
- [ ] **DB-015** Indexes: communications (tenant, created_at), tasks (assigned_to, status)

### DevOps (Support)
- [ ] **DV-013** WhatsApp provider webhook endpoint + verification
- [ ] **DV-014** Email/SMS webhook endpoints
- [ ] **DV-015** Rate limiting: provider API limits

### Definition of Done (Sprint 4)
- [ ] Create template → schedule → reminders sent automatically
- [ ] Deduplication works (no double-send)
- [ ] Skip rules respected (paid/disputed/opt-out)
- [ ] Communication log shows sent/delivered/failed
- [ ] Fallback: WhatsApp fails → Email

---

## Sprint 5: Payments (Week 9-10)
**Goal**: Payment links created, customers can pay, reconciliation works

### Backend (Lead)
- [ ] **BE-038** PaymentLink CRUD + Razorpay integration
- [ ] **BE-039** Razorpay webhook: `POST /api/v1/payments/webhook/razorpay`
- [ ] **BE-040** Webhook idempotency: `razorpay_payment_id` unique constraint
- [ ] **BE-041** Payment reconciliation: link payment → invoice → update outstanding
- [ ] **BE-042** Partial payment handling
- [ ] **BE-043** Public payment page: `GET /pay/{token}`, `POST /pay/{token}/initiate`
- [ ] **BE-044** Payment history endpoint

### Frontend (Lead)
- [ ] **FE-022** Payment Links page: create, list, cancel, copy link
- [ ] **FE-023** Payment history: filter, export
- [ ] **FE-024** Public payment page: amount, UPI/Card/NetBanking, success page
- [ ] **FE-025** Invoice detail: "Send Payment Link" button

### Database Optimizer (Lead)
- [ ] **DB-016** Models + migrations: PaymentLink, Payment (extend)
- [ ] **DB-017** Unique index: payments (razorpay_payment_id)
- [ ] **DB-018** Indexes: payment_links (tenant, status, expires_at)

### DevOps (Lead)
- [ ] **DV-016** Razorpay webhook URL configuration (ngrok for local, domain for staging)
- [ ] **DV-017** SSL/TLS for payment page
- [ ] **DV-018** PCI compliance notes (no card data stored)
- [ ] **DV-019** Load test: 100 concurrent payments

### Definition of Done (Sprint 5)
- [ ] Create payment link → customer pays → invoice marked paid
- [ ] Webhook processes payment, updates outstanding
- [ ] Partial payment reduces outstanding correctly
- [ ] Public payment page works end-to-end

---

## Sprint 6: Dashboard + Launch (Week 11-12)
**Goal**: Production-ready with KPIs, charts, polish

### Backend (Lead)
- [ ] **BE-045** Dashboard summary: KPIs, aging breakdown, top debtors
- [ ] **BE-046** DSO calculation (30d, 90d, FY)
- [ ] **BE-047** Cash flow forecast (12 weeks)
- [ ] **BE-048** Collection efficiency metric
- [ ] **BE-049** Customer risk score algorithm
- [ ] **BE-050** Report endpoints: aging, outstanding, collection
- [ ] **BE-051** Settings: Team, Tally, Templates, Schedule, Billing
- [ ] **BE-052** Audit logging on all mutations
- [ ] **BE-053** Performance optimization: query analysis, caching

### Frontend (Lead)
- [ ] **FE-026** Dashboard: KPI cards, aging chart (Recharts), top debtors table
- [ ] **FE-027** Aging chart: trend over time
- [ ] **FE-028** Cash flow forecast: area chart
- [ ] **FE-029** DSO trend: line chart
- [ ] **FE-030** Reports page: Aging, Outstanding, Collection
- [ ] **FE-031** Settings pages: Team, Tally, Templates, Schedule, Billing
- [ ] **FE-032** Responsive polish: tablet/mobile dashboard
- [ ] **FE-033** Error boundaries, loading skeletons, empty states
- [ ] **FE-034** Dark mode support

### Database Optimizer (Lead)
- [ ] **DB-019** Dashboard snapshot table + materialized view
- [ ] **DB-020** Customer risk scores table + computation job
- [ ] **DB-021** Final index review + query plan analysis
- [ ] **DB-022** Backup/restore test

### DevOps (Lead)
- [ ] **DV-020** Production Azure resources: PostgreSQL, Redis, Blob, Key Vault, Container Apps, Front Door
- [ ] **DV-021** Production deploy pipeline: staging → prod (manual approval)
- [ ] **DV-022** DNS + SSL (custom domain)
- [ ] **DV-023** Monitoring alerts: error rate, queue depth, disk, CPU
- [ ] **DV-024** Runbooks: common incidents
- [ ] **DV-025** Load test: 100 concurrent users, dashboard < 2s
- [ ] **DV-026** Security scan: OWASP ZAP, dependency audit
- [ ] **DV-027** Launch checklist

### All (Support)
- [ ] **ALL-001** Bug bash (2 days)
- [ ] **ALL-002** Documentation: API docs, user guide, runbooks
- [ ] **ALL-003** Demo to stakeholders

### Definition of Done (Sprint 6)
- [ ] Dashboard loads < 2s with 50k invoices
- [ ] All charts render correctly
- [ ] Production deployed and accessible
- [ ] Monitoring alerts firing correctly
- [ ] Launch checklist 100% complete

---

## Critical Path

```
Sprint 1 (DV-002, DV-003, BE-001-010) 
    → Sprint 2 (BE-011-018, FE-007-010)
        → Sprint 3 (BE-019-027, FE-011-016, DB-007-011)
            → Sprint 4 (BE-028-037, FE-017-021)
                → Sprint 5 (BE-038-044, FE-022-025, DV-016-019)
                    → Sprint 6 (BE-045-053, FE-026-034, DV-020-027)
```

**Blocking Dependencies:**
1. **DV-002/003** (infra) → Blocks all backend/frontend work
2. **BE-001-006** (auth) → Blocks frontend login
3. **BE-013** (sync endpoint) → Blocks Sprint 2 frontend
4. **BE-022** (aging calc) → Blocks Sprint 3 frontend aging page
5. **DV-016** (Razorpay webhook) → Blocks Sprint 5 payment testing

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tally XML parsing complexity | High | High | Mock server first, real Tally testing week 3 |
| WhatsApp provider approval delay | Medium | High | Apply week 1, build email fallback first |
| DevOps bottleneck | High | Medium | DevOps pairs with BE sprint 1-2 |
| Scope creep | Very High | Critical | Weekly scope review, MVP only |
| Performance at scale | Low | High | Load test sprint 3, 5, 6 |
| Azure subscription delay | Medium | Medium | Local-first, deploy when ready |

---

## Team Capacity (Per Sprint)

| Role | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 |
|------|----------|----------|----------|----------|----------|----------|
| Backend | 100% | 100% | 100% | 100% | 100% | 80% |
| Frontend | 60% | 20% | 100% | 100% | 100% | 100% |
| Database | 40% | 60% | 100% | 80% | 60% | 100% |
| DevOps | 100% | 60% | 40% | 40% | 60% | 100% |

---

## GitHub Issue Labels
- `sprint:1` through `sprint:6`
- `area:backend`, `area:frontend`, `area:database`, `area:devops`
- `type:feature`, `type:bug`, `type:chore`, `type:docs`
- `priority:critical`, `priority:high`, `priority:medium`, `priority:low`
- `blocked` (for dependencies)