# CredFlow Domain Model (DDD)

## Bounded Contexts (7 Domains)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CRED FLOW PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   IDENTITY   │  │    TALLY     │  │  RECEIVABLES    │  │ COLLECTIONS │  │
│  │              │  │              │  │                 │  │             │  │
│  │ • Tenants    │  │ • Agents     │  │ • Customers     │  │ • Templates │  │
│  │ • Users      │  │ • Companies  │  │ • Invoices      │  │ • Campaigns │  │
│  │ • Roles      │  │ • Sync Logs  │  │ • Payments      │  │ • Tasks     │  │
│  │ • Invitations│  │ • Field Map  │  │ • Aging         │  │ • Disputes  │  │
│  │ • Auth       │  │ • Delta Sync │  │ • DSO           │  │ • Comm Log  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  └──────┬──────┘  │
│         │                 │                   │                  │         │
│         └─────────────────┼───────────────────┼──────────────────┘         │
│                           ▼                   ▼                            │
│                    ┌──────────────┐  ┌─────────────────┐                   │
│                    │   PAYMENTS   │  │   ANALYTICS     │                   │
│                    │              │  │                 │                   │
│                    │ • Links      │  │ • Dashboards    │                   │
│                    │ • Webhooks   │  │ • Aging Reports │                   │
│                    │ • Reconcile  │  │ • Cash Flow     │                   │
│                    │ • Refunds    │  │ • Risk Scores   │                   │
│                    └──────┬───────┘  └────────┬────────┘                   │
│                           │                   │                            │
│                           └───────────┬───────┘                            │
│                                       ▼                                    │
│                              ┌──────────────┐                              │
│                              │NOTIFICATIONS │                              │
│                              │              │                              │
│                              │ • WhatsApp   │                              │
│                              │ • Email      │                              │
│                              │ • SMS        │                              │
│                              │ • Templates  │                              │
│                              │ • Providers  │                              │
│                              └──────────────┘                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Domain Details

### 1. IDENTITY DOMAIN
**Responsibility**: Tenant management, authentication, authorization, user lifecycle

**Aggregates**:
- `Tenant` (Root): `id`, `name`, `subdomain`, `status`, `settings`, `billing_plan`, `created_at`
- `User` (Root): `id`, `tenant_id`, `email`, `name`, `role`, `status`, `last_login_at`
- `Invitation` (Root): `id`, `tenant_id`, `email`, `role`, `token`, `expires_at`, `accepted_at`

**Domain Events**:
- `TenantCreated`, `TenantActivated`, `TenantSuspended`
- `UserInvited`, `UserJoined`, `UserRoleChanged`, `UserDeactivated`
- `AgentRegistered`, `AgentHeartbeatReceived`, `AgentOffline`

**Policies**:
- Tenant isolation enforced at all layers
- Super Admin can manage all tenants
- Tenant Admin manages users within tenant
- Agent authentication via API key (separate from user auth)

---

### 2. TALLY DOMAIN
**Responsibility**: Tally agent management, data synchronization, XML parsing

**Aggregates**:
- `Agent` (Root): `id`, `tenant_id`, `name`, `api_key_hash`, `status`, `last_heartbeat`, `config`, `version`
- `TallyCompany` (Root): `id`, `tenant_id`, `agent_id`, `tally_guid`, `name`, `financial_year_start`, `last_synced_at`
- `SyncLog` (Root): `id`, `tenant_id`, `agent_id`, `company_id`, `entity_type`, `records_processed`, `status`, `error_details`, `started_at`, `completed_at`

**Value Objects**:
- `TallyXMLRequest` / `TallyXMLResponse` (parsing logic)
- `FieldMapping` (Tally field → DB column)
- `SyncCursor` (last sync timestamp per entity type)

**Domain Events**:
- `SyncStarted`, `SyncCompleted`, `SyncFailed`
- `CompanyDiscovered`, `CompanyLinked`
- `AgentConnected`, `AgentDisconnected`, `AgentUpdated`

**Policies**:
- One agent per tenant (MVP), multiple companies per agent
- Delta sync: only changed records since last successful sync
- Sync payload size limit: 50MB (configurable)
- Failed syncs retry with exponential backoff (max 3 retries)

---

### 3. RECEIVABLES DOMAIN
**Responsibility**: Customer, invoice, payment management, aging analysis

**Aggregates**:
- `Customer` (Root): `id`, `tenant_id`, `tally_ledger_guid`, `name`, `gstin`, `address`, `contact_person`, `phone`, `email`, `credit_limit`, `payment_terms_days`, `risk_score`, `status`, `outstanding_amount`
- `Invoice` (Root): `id`, `tenant_id`, `customer_id`, `tally_voucher_id`, `voucher_number`, `voucher_date`, `due_date`, `amount`, `tax_amount`, `total_amount`, `outstanding_amount`, `status` (draft/sent/partial/paid/overdue/disputed/cancelled), `gstin`, `place_of_supply`
- `Payment` (Root): `id`, `tenant_id`, `customer_id`, `invoice_id`, `tally_receipt_id`, `amount`, `payment_date`, `payment_mode`, `reference_number`, `status`, `razorpay_payment_id`, `razorpay_link_id`

**Value Objects**:
- `AgingBucket` (CURRENT, D1_30, D31_60, D61_90, D91_180, D180_PLUS)
- `Money` (amount, currency=INR)
- `GSTBreakdown` (cgst, sgst, igst, cess)

**Domain Events**:
- `InvoiceCreated`, `InvoiceUpdated`, `InvoicePaid`, `InvoiceOverdue`, `InvoiceDisputed`
- `PaymentReceived`, `PaymentMatched`, `PaymentFailed`
- `CustomerRiskScoreChanged`, `CreditLimitExceeded`

**Calculations** (Pure Functions):
```python
def calculate_aging_bucket(due_date: date, as_of: date) -> AgingBucket:
    days_overdue = (as_of - due_date).days
    if days_overdue <= 0: return AgingBucket.CURRENT
    elif days_overdue <= 30: return AgingBucket.D1_30
    elif days_overdue <= 60: return AgingBucket.D31_60
    elif days_overdue <= 90: return AgingBucket.D61_90
    elif days_overdue <= 180: return AgingBucket.D91_180
    else: return AgingBucket.D180_PLUS

def calculate_dso(outstanding: Money, sales: Money, period_days: int) -> float:
    if sales.amount == 0: return 0
    return float(outstanding.amount / sales.amount * period_days)

def calculate_collection_efficiency(collected: Money, invoiced: Money) -> float:
    if invoiced.amount == 0: return 100
    return float(collected.amount / invoiced.amount * 100)
```

**Policies**:
- Invoice status transitions: draft → sent → partial/paid/overdue/disputed/cancelled
- Aging recalculated hourly via scheduler
- DSO calculated daily for 30/90/FY periods
- Outstanding amount = total_amount - sum(payments) - credit_notes

---

### 4. COLLECTIONS DOMAIN
**Responsibility**: Reminder campaigns, communication templates, collection tasks, disputes

**Aggregates**:
- `ReminderTemplate` (Root): `id`, `tenant_id`, `name`, `channel` (whatsapp/email/sms), `subject`, `body`, `variables`, `days_before_due`, `days_after_due`, `is_active`
- `CollectionCampaign` (Root): `id`, `tenant_id`, `name`, `template_id`, `filter_criteria`, `schedule`, `status`, `last_run_at`
- `Communication` (Root): `id`, `tenant_id`, `customer_id`, `invoice_id`, `template_id`, `channel`, `recipient`, `subject`, `body`, `status` (pending/sent/delivered/failed/bounced), `provider_message_id`, `sent_at`, `delivered_at`, `error`
- `CollectionTask` (Root): `id`, `tenant_id`, `assigned_to`, `customer_id`, `invoice_id`, `type` (call/email/visit), `priority`, `due_date`, `status`, `notes`, `completed_at`
- `Dispute` (Root): `id`, `tenant_id`, `invoice_id`, `customer_id`, `reason`, `description`, `status` (open/under_review/resolved/rejected), `resolution`, `created_at`, `resolved_at`

**Domain Events**:
- `ReminderTemplateCreated`, `ReminderTemplateUpdated`
- `CampaignStarted`, `CampaignCompleted`
- `CommunicationSent`, `CommunicationDelivered`, `CommunicationFailed`
- `TaskCreated`, `TaskAssigned`, `TaskCompleted`
- `DisputeRaised`, `DisputeResolved`

**Policies**:
- Deduplication: One reminder per (invoice, channel, date) combination
- Skip conditions: Paid, Disputed, Opted-out, Promised date not past
- Channel priority: WhatsApp → Email → SMS (configurable)
- Template variables: `{{customer_name}}`, `{{invoice_number}}`, `{{amount}}`, `{{due_date}}`, `{{payment_link}}`, `{{days_overdue}}`

---

### 5. PAYMENTS DOMAIN
**Responsibility**: Payment links, Razorpay integration, reconciliation

**Aggregates**:
- `PaymentLink` (Root): `id`, `tenant_id`, `invoice_id`, `customer_id`, `amount`, `currency`, `description`, `expires_at`, `status` (active/paid/expired/cancelled), `razorpay_link_id`, `razorpay_link_url`, `created_at`, `paid_at`
- `PaymentTransaction` (Root): `id`, `tenant_id`, `payment_link_id`, `invoice_id`, `amount`, `currency`, `payment_method`, `razorpay_payment_id`, `razorpay_order_id`, `status`, `captured_at`, `fee_amount`, `gst_on_fee`

**Domain Events**:
- `PaymentLinkCreated`, `PaymentLinkExpired`, `PaymentLinkCancelled`
- `PaymentReceived`, `PaymentCaptured`, `PaymentFailed`, `PaymentRefunded`
- `PaymentReconciled`, `PaymentMismatched`

**Policies**:
- Default link expiry: 30 days (configurable per tenant)
- Partial payments: Create new PaymentTransaction, reduce invoice outstanding
- Overpayments: Flag for review, create credit note
- Idempotency: Razorpay webhook processed exactly once via `razorpay_payment_id` unique constraint

---

### 6. ANALYTICS DOMAIN
**Responsibility**: Dashboards, reports, forecasting, risk scoring

**Aggregates**:
- `DashboardSnapshot` (Root): `id`, `tenant_id`, `period`, `total_outstanding`, `overdue_amount`, `dso`, `collection_efficiency`, `top_debtors`, `aging_breakdown`, `cash_flow_forecast`, `computed_at`
- `CustomerRiskScore` (Root): `id`, `tenant_id`, `customer_id`, `score` (0-100), `risk_level` (LOW/MEDIUM/HIGH), `factors`, `computed_at`

**Read Models (Projections)**:
- `AgingReport`: Customer × AgingBucket matrix
- `OutstandingReport`: Invoice-level detail with days overdue
- `CollectionReport`: Campaign effectiveness, channel performance
- `CashFlowForecast`: Weekly projected inflows for 12 weeks

**Domain Events**:
- `DashboardRefreshed`, `ReportGenerated`
- `RiskScoreUpdated`

**Calculations**:
```python
# Risk Score Factors (weighted)
RISK_FACTORS = {
    "days_overdue_avg": 0.30,
    "payment_history": 0.25,
    "outstanding_trend": 0.20,
    "dispute_count": 0.15,
    "credit_utilization": 0.10,
}

def calculate_risk_score(customer: Customer, invoices: List[Invoice]) -> int:
    # Normalize each factor 0-100, apply weights, sum
    pass

# Cash Flow Forecast (simplified)
def forecast_cash_flow(invoices: List[Invoice], weeks: int = 12) -> List[WeeklyForecast]:
    # Group by expected payment week based on:
    # - Due date + payment terms
    # - Customer historical payment behavior
    # - Promise dates if any
    pass
```

---

### 7. NOTIFICATIONS DOMAIN
**Responsibility**: Multi-channel messaging, provider management, template rendering

**Aggregates**:
- `NotificationProvider` (Root): `id`, `tenant_id`, `channel` (whatsapp/email/sms), `provider_type`, `config` (encrypted), `is_active`, `is_default`
- `NotificationTemplate` (Root): `id`, `tenant_id`, `channel`, `name`, `subject`, `body`, `variables`, `language`

**Domain Events**:
- `ProviderConfigured`, `ProviderTested`
- `TemplateCreated`, `TemplateUpdated`
- `MessageQueued`, `MessageSent`, `MessageDelivered`, `MessageFailed`

**Policies**:
- Provider config encrypted at rest (AES-256 via libsodium)
- Fallback chain: Primary provider → Secondary provider
- Rate limiting per provider (respect API limits)
- Opt-out handling per channel per customer

---

## Cross-Domain Events (Event-Driven Integration)

| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `InvoiceCreated` | Receivables | Collections (schedule reminders), Analytics (update dashboard) |
| `InvoicePaid` | Receivables | Collections (stop reminders), Payments (reconcile), Analytics |
| `PaymentReceived` | Payments | Receivables (update invoice), Collections (stop reminders) |
| `CustomerRiskScoreChanged` | Receivables | Collections (prioritize tasks), Analytics |
| `DisputeRaised` | Collections | Receivables (pause reminders), Analytics |
| `SyncCompleted` | Tally | Receivables (trigger aging recalc), Analytics |

---

## Anti-Corruption Layers

| Boundary | ACL Responsibility |
|----------|-------------------|
| Tally → Receivables | XML parsing, field mapping, data validation, GUID→UUID conversion |
| Razorpay → Payments | Webhook verification, idempotency, status mapping |
| WhatsApp/Email/SMS → Notifications | Provider-specific payload formatting, error normalization |
| Keycloak/Entra ID → Identity | Token validation, claim mapping, role synchronization |

---

## Ubiquitous Language (Glossary)

| Term | Definition |
|------|------------|
| **Tenant** | A single SME company using CredFlow (multi-tenant isolation) |
| **Agent** | Local Go binary running on customer's Windows machine |
| **Tally Company** | A company within Tally ERP (one agent can sync multiple) |
| **Ledger** | Tally term for Customer/Supplier master record |
| **Voucher** | Tally term for transaction (Sales=Invoice, Receipt=Payment) |
| **Aging Bucket** | Time-based categorization of overdue invoices |
| **DSO** | Days Sales Outstanding - average collection period |
| **Payment Link** | Razorpay-hosted page for customer to pay invoice |
| **Campaign** | Automated reminder sequence for a customer segment |
| **Dispute** | Customer-raised issue on an invoice (pauses reminders) |