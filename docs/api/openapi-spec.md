# CredFlow OpenAPI 3.0 Specification

## Overview
This document defines the complete API contract for CredFlow v1. All endpoints are prefixed with `/api/v1/`.

## Base Configuration
- **Base URL**: `https://api.credflow.in/api/v1` (production) / `http://localhost:8000/api/v1` (local)
- **Authentication**: Bearer token (JWT) in `Authorization` header
- **Tenant Context**: Extracted from JWT `tenant_id` claim
- **Content-Type**: `application/json`
- **Date Format**: ISO 8601 (UTC), e.g., `2024-01-15T10:30:00Z`
- **Pagination**: Cursor-based for large datasets, offset for small

## Standard Response Format

```json
{
  "success": true,
  "data": {},
  "meta": {
    "pagination": {
      "next_cursor": "eyJpZCI6MTIzfQ==",
      "has_more": true,
      "total": 150
    }
  },
  "error": null
}
```

## Standard Error Format

```json
{
  "success": false,
  "data": null,
  "meta": null,
  "error": {
    "code": "INVOICE_NOT_FOUND",
    "message": "Invoice with id 'xxx' not found",
    "details": {
      "invoice_id": "xxx",
      "tenant_id": "yyy"
    }
  }
}
```

## HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/expired token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate, idempotency) |
| 422 | Unprocessable Entity (business rule violation) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Error Codes
| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Request body validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `TOKEN_EXPIRED` | 401 | Access token expired, use refresh token |
| `FORBIDDEN` | 403 | Insufficient permissions for resource |
| `TENANT_NOT_FOUND` | 404 | Tenant not found or suspended |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists |
| `IDEMPOTENCY_KEY_CONFLICT` | 409 | Idempotency key already used |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependency unavailable |

## Pagination

### Cursor-based (Large datasets - invoices, communications, audit_logs)
```
GET /api/v1/invoices?cursor=eyJpZCI6MTIzfQ==&limit=50
```
Response meta:
```json
{
  "pagination": {
    "next_cursor": "eyJpZCI6MTczfQ==",
    "has_more": true,
    "total": 1250
  }
}
```

### Offset-based (Small datasets - templates, tasks, users)
```
GET /api/v1/templates?offset=0&limit=20
```
Response meta:
```json
{
  "pagination": {
    "offset": 0,
    "limit": 20,
    "total": 45
  }
}
```

---

## AUTH ENDPOINTS

### POST /api/v1/auth/register
Register a new tenant and admin user.

**Request:**
```json
{
  "tenant_name": "ABC Trading Co",
  "subdomain": "abc-trading",
  "admin_email": "admin@abc.com",
  "admin_name": "Admin User",
  "password": "securePassword123"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "tenant": { "id": "uuid", "name": "ABC Trading Co", "subdomain": "abc-trading" },
    "user": { "id": "uuid", "email": "admin@abc.com", "role": "tenant_admin" },
    "tokens": { "access_token": "...", "refresh_token": "...", "expires_in": 900 }
  }
}
```

### POST /api/v1/auth/login
Authenticate user with email/password.

**Request:**
```json
{
  "email": "admin@abc.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": { "id": "uuid", "email": "admin@abc.com", "name": "Admin", "role": "tenant_admin", "tenant_id": "uuid" },
    "tokens": { "access_token": "...", "refresh_token": "...", "expires_in": 900 }
  }
}
```

### POST /api/v1/auth/callback
OIDC callback from Keycloak/Azure Entra ID.

**Request:**
```json
{
  "code": "auth_code_from_provider",
  "state": "csrf_state_token"
}
```

**Response (200):** Same as login

### POST /api/v1/auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "refresh_token_from_login"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 900
  }
}
```

### POST /api/v1/auth/logout
Revoke refresh token.

**Request:**
```json
{
  "refresh_token": "token_to_revoke"
}
```

**Response (200):**
```json
{ "success": true, "data": { "message": "Logged out successfully" } }
```

### GET /api/v1/auth/me
Get current user profile.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "admin@abc.com",
      "name": "Admin User",
      "role": "tenant_admin",
      "permissions": ["invoices:read", "invoices:write", "customers:read", ...],
      "tenant": { "id": "uuid", "name": "ABC Trading Co", "subdomain": "abc-trading" }
    }
  }
}
```

### POST /api/v1/auth/invite/{token}
Accept invitation and set password.

**Request:**
```json
{
  "password": "newPassword123",
  "name": "New User"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": { "id": "uuid", "email": "user@abc.com", "role": "analyst" },
    "tokens": { "access_token": "...", "refresh_token": "...", "expires_in": 900 }
  }
}
```

---

## AGENT ENDPOINTS

### POST /api/v1/agents/register
Register a new Tally agent (requires super_admin or tenant_admin).

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "name": "Office Desktop",
  "tally_url": "http://localhost:9000",
  "sync_interval_minutes": 15
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "agent": {
      "id": "uuid",
      "name": "Office Desktop",
      "api_key": "cf_abc123...", // Only returned once!
      "status": "inactive"
    }
  }
}
```

### POST /api/v1/agents/heartbeat
Agent heartbeat (called by agent every 5 min).

**Headers:** `X-Agent-Key: cf_abc123...`

**Request:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "last_sync_at": "2024-01-15T10:00:00Z"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "agent_id": "uuid",
    "server_time": "2024-01-15T10:05:00Z",
    "config_update_available": false
  }
}
```

### GET /api/v1/agents
List agents for current tenant.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?status=active&limit=20&offset=0`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Office Desktop",
      "status": "active",
      "last_heartbeat_at": "2024-01-15T10:05:00Z",
      "version": "1.0.0",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": { "pagination": { "offset": 0, "limit": 20, "total": 1 } }
}
```

### DELETE /api/v1/agents/{id}
Deactivate agent.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{ "success": true, "data": { "message": "Agent deactivated" } }
```

---

## TALLY SYNC ENDPOINTS

### POST /api/v1/tally/sync
Receive sync payload from Tally agent.

**Headers:** `X-Agent-Key: cf_abc123...` (or `Authorization: Bearer <jwt>` for manual trigger)

**Request:**
```json
{
  "company_id": "tally_guid",
  "synced_at": "2024-01-15T10:00:00Z",
  "customers": [
    {
      "tally_ledger_guid": "guid",
      "name": "Reliance Industries Ltd",
      "gstin": "27AAACR5055K1ZP",
      "address": { "line1": "...", "city": "Mumbai", "state": "Maharashtra", "pincode": "400021" },
      "contact_person": "John Doe",
      "phone": "9876543210",
      "email": "accounts@reliance.com",
      "credit_limit": 1000000,
      "payment_terms_days": 30
    }
  ],
  "invoices": [
    {
      "tally_voucher_id": "voucher_guid",
      "voucher_number": "1",
      "voucher_date": "2024-01-15",
      "due_date": "2024-02-14",
      "customer_tally_guid": "customer_guid",
      "amount": 1000000,
      "tax_amount": 180000,
      "total_amount": 1180000,
      "gstin": "27AAACR5055K1ZP",
      "place_of_supply": "Maharashtra"
    }
  ],
  "payments": [
    {
      "tally_receipt_id": "receipt_guid",
      "invoice_tally_voucher_id": "voucher_guid",
      "customer_tally_guid": "customer_guid",
      "amount": 1180000,
      "payment_date": "2024-02-10",
      "payment_mode": "bank_transfer",
      "reference_number": "UTIB123456"
    }
  ]
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "sync_id": "uuid",
    "status": "queued",
    "message": "Sync queued for processing"
  }
}
```

### GET /api/v1/tally/companies
List Tally companies for current tenant.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "tally_guid": "guid",
      "name": "ABC Trading Co.",
      "financial_year_start": "2024-04-01",
      "last_synced_at": "2024-01-15T10:00:00Z",
      "agent_name": "Office Desktop"
    }
  ]
}
```

### GET /api/v1/tally/sync-logs
Get sync history.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?company_id=uuid&status=failed&limit=50&cursor=...`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "company_id": "uuid",
      "entity_type": "invoices",
      "records_processed": 150,
      "status": "completed",
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:00:05Z"
    }
  ],
  "meta": { "pagination": { "next_cursor": "...", "has_more": true } }
}
```

### POST /api/v1/tally/sync/trigger
Manually trigger sync for a company.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "company_id": "uuid",
  "entity_types": ["customers", "invoices", "payments"]
}
```

**Response (202):**
```json
{
  "success": true,
  "data": { "sync_id": "uuid", "status": "triggered" }
}
```

---

## CUSTOMER ENDPOINTS

### GET /api/v1/customers
List customers with filters.

**Headers:** `Authorization: Bearer <jwt>`

**Query:**
```
?search=reliance
&status=active
&gstin=27AAACR5055K1ZP
&risk_level=HIGH
&has_outstanding=true
&sort=name:asc
&limit=50
&cursor=...
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Reliance Industries Ltd",
      "gstin": "27AAACR5055K1ZP",
      "contact_person": "John Doe",
      "phone": "9876543210",
      "email": "accounts@reliance.com",
      "credit_limit": 1000000,
      "payment_terms_days": 30,
      "risk_score": 85,
      "risk_level": "HIGH",
      "outstanding_amount": 1250000,
      "open_invoice_count": 3,
      "oldest_due_date": "2023-12-01",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": { "pagination": { "next_cursor": "...", "has_more": true, "total": 125 } }
}
```

### GET /api/v1/customers/{id}
Get customer detail.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Reliance Industries Ltd",
    "gstin": "27AAACR5055K1ZP",
    "address": { "line1": "Maker Chambers IV", "city": "Mumbai", "state": "Maharashtra", "pincode": "400021" },
    "contact_person": "John Doe",
    "phone": "9876543210",
    "email": "accounts@reliance.com",
    "credit_limit": 1000000,
    "payment_terms_days": 30,
    "risk_score": 85,
    "risk_level": "HIGH",
    "outstanding_amount": 1250000,
    "open_invoice_count": 3,
    "total_invoice_count": 12,
    "total_paid_amount": 5000000,
    "average_payment_days": 45,
    "last_payment_date": "2024-01-10",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### PUT /api/v1/customers/{id}
Update customer (credit limit, payment terms, contact info).

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "credit_limit": 1500000,
  "payment_terms_days": 45,
  "contact_person": "Jane Smith",
  "phone": "9876543211",
  "email": "finance@reliance.com"
}
```

**Response (200):** Updated customer object

### GET /api/v1/customers/{id}/invoices
Get customer's invoices.

**Query:** `?status=overdue&limit=50&cursor=...`

**Response (200):** Paginated invoice list

### GET /api/v1/customers/{id}/payments
Get customer's payment history.

**Query:** `?from_date=2024-01-01&to_date=2024-12-31&limit=50`

**Response (200):** Paginated payment list

### GET /api/v1/customers/{id}/timeline
Get customer activity timeline (invoices, payments, communications, tasks).

**Query:** `?limit=100&cursor=...`

**Response (200):**
```json
{
  "success": true,
  "data": [
    { "type": "invoice_created", "date": "2024-01-15", "invoice_id": "uuid", "amount": 1180000 },
    { "type": "payment_received", "date": "2024-02-10", "payment_id": "uuid", "amount": 1180000 },
    { "type": "reminder_sent", "date": "2024-02-01", "channel": "whatsapp", "template": "Due Soon" }
  ]
}
```

---

## INVOICE ENDPOINTS

### GET /api/v1/invoices
List invoices with filters.

**Headers:** `Authorization: Bearer <jwt>`

**Query:**
```
?status=overdue
&customer_id=uuid
&from_date=2024-01-01
&to_date=2024-12-31
&min_amount=10000
&max_amount=1000000
&aging_bucket=D31_60
&sort=due_date:asc
&limit=50
&cursor=...
```

**Response (200):** Paginated invoice list

### GET /api/v1/invoices/{id}
Get invoice detail with payment history.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "customer": { "id": "uuid", "name": "Reliance Industries Ltd" },
    "voucher_number": "1",
    "voucher_date": "2024-01-15",
    "due_date": "2024-02-14",
    "amount": 1000000,
    "tax_amount": 180000,
    "total_amount": 1180000,
    "outstanding_amount": 1180000,
    "status": "sent",
    "gstin": "27AAACR5055K1ZP",
    "place_of_supply": "Maharashtra",
    "payments": [
      { "id": "uuid", "amount": 500000, "payment_date": "2024-02-10", "mode": "bank_transfer" }
    ],
    "aging_bucket": "D1_30",
    "days_overdue": 15,
    "payment_link": { "id": "uuid", "url": "https://pay.credflow.in/pay/abc", "expires_at": "2024-03-15" }
  }
}
```

### GET /api/v1/invoices/aging
Get aging analysis summary.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?as_of_date=2024-01-31&customer_id=uuid`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "as_of_date": "2024-01-31",
    "buckets": {
      "CURRENT": { "count": 45, "amount": 2500000 },
      "D1_30": { "count": 12, "amount": 800000 },
      "D31_60": { "count": 8, "amount": 650000 },
      "D61_90": { "count": 3, "amount": 320000 },
      "D91_180": { "count": 2, "amount": 180000 },
      "D180_PLUS": { "count": 1, "amount": 95000 }
    },
    "total_outstanding": 4545000,
    "total_overdue": 2045000,
    "overdue_percentage": 45.0
  }
}
```

### GET /api/v1/invoices/overdue
Get overdue invoices (shortcut for status=overdue).

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?days_overdue_min=1&limit=100`

**Response (200):** Paginated overdue invoices

---

## COLLECTIONS ENDPOINTS

### GET /api/v1/templates
List reminder templates.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?channel=whatsapp&is_active=true`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Due Soon - WhatsApp",
      "channel": "whatsapp",
      "subject": "",
      "body": "Dear {{customer_name}}, your invoice {{invoice_number}} of ₹{{amount}} is due on {{due_date}}.",
      "variables": ["customer_name", "invoice_number", "amount", "due_date", "payment_link"],
      "days_before_due": 3,
      "days_after_due": 0,
      "is_active": true
    }
  ]
}
```

### POST /api/v1/templates
Create reminder template.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "name": "Overdue - Email",
  "channel": "email",
  "subject": "Invoice {{invoice_number}} Overdue",
  "body": "Dear {{customer_name}},\n\nInvoice {{invoice_number}} (₹{{amount}}) was due on {{due_date}}.",
  "variables": ["customer_name", "invoice_number", "amount", "due_date"],
  "days_before_due": 0,
  "days_after_due": 7,
  "is_active": true
}
```

**Response (201):** Created template

### PUT /api/v1/templates/{id}
Update template.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):** Updated template

### DELETE /api/v1/templates/{id}
Delete template.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):** `{ "success": true, "data": { "message": "Template deleted" } }`

### POST /api/v1/reminders/send
Manually trigger reminder for specific invoices.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "invoice_ids": ["uuid1", "uuid2"],
  "template_id": "uuid",
  "channel": "whatsapp"
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "queued": 2,
    "skipped": 0,
    "message": "Reminders queued for sending"
  }
}
```

### GET /api/v1/communications
List communications history.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?customer_id=uuid&invoice_id=uuid&channel=whatsapp&status=failed&from_date=2024-01-01&limit=50&cursor=...`

**Response (200):** Paginated communications

### GET /api/v1/tasks
List collection tasks.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?assigned_to_me=true&status=pending&priority=high&due_before=2024-01-31`

**Response (200):** Paginated tasks

### POST /api/v1/tasks
Create collection task.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "customer_id": "uuid",
  "invoice_id": "uuid",
  "type": "call",
  "priority": "high",
  "due_date": "2024-01-20",
  "notes": "Customer promised payment by Friday"
}
```

**Response (201):** Created task

### PUT /api/v1/tasks/{id}
Update task (status, notes, reassignment).

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):** Updated task

---

## PAYMENT ENDPOINTS

### POST /api/v1/payment-links
Create payment link for invoice.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "invoice_id": "uuid",
  "expires_in_days": 30,
  "description": "Payment for Invoice INV-2024-001"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_id": "uuid",
    "amount": 1180000,
    "currency": "INR",
    "razorpay_link_id": "plink_xxx",
    "razorpay_link_url": "https://rzp.io/i/xxx",
    "expires_at": "2024-02-15T00:00:00Z",
    "status": "active"
  }
}
```

### GET /api/v1/payment-links
List payment links.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?status=active&invoice_id=uuid&limit=50`

**Response (200):** Paginated payment links

### DELETE /api/v1/payment-links/{id}
Cancel payment link.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):** `{ "success": true, "data": { "message": "Payment link cancelled" } }`

### POST /api/v1/payments/webhook/razorpay
Razorpay webhook endpoint (public, no auth).

**Headers:** `X-Razorpay-Signature: <signature>`

**Request:** Razorpay webhook payload

**Response (200):**
```json
{ "success": true, "data": { "message": "Webhook processed" } }
```

### GET /api/v1/payments
List payment transactions.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?from_date=2024-01-01&to_date=2024-12-31&status=completed&limit=50`

**Response (200):** Paginated payments

---

## DASHBOARD ENDPOINTS

### GET /api/v1/dashboard/summary
Get dashboard KPI summary.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_outstanding": 4545000,
    "overdue_amount": 2045000,
    "overdue_percentage": 45.0,
    "total_customers": 125,
    "customers_with_overdue": 38,
    "dso": 42.5,
    "collection_efficiency": 78.3,
    "invoices_due_this_week": 12,
    "invoices_overdue": 25,
    "payments_received_this_month": 1500000,
    "top_debtors": [
      { "customer_id": "uuid", "name": "Adani Enterprises", "outstanding": 1890000, "risk_level": "HIGH" },
      { "customer_id": "uuid", "name": "Reliance Industries", "outstanding": 1250000, "risk_level": "HIGH" }
    ],
    "aging_breakdown": {
      "CURRENT": 2500000,
      "D1_30": 800000,
      "D31_60": 650000,
      "D61_90": 320000,
      "D91_180": 180000,
      "D180_PLUS": 95000
    }
  }
}
```

### GET /api/v1/dashboard/aging
Get aging chart data.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?period=30d` (30d, 90d, 1y)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "data": [
      { "date": "2024-01-01", "current": 2500000, "d1_30": 800000, "d31_60": 650000, "d61_90": 320000, "d91_180": 180000, "d180_plus": 95000 },
      { "date": "2024-01-08", "current": 2400000, "d1_30": 850000, "d31_60": 600000, "d61_90": 350000, "d91_180": 180000, "d180_plus": 100000 }
    ]
  }
}
```

### GET /api/v1/dashboard/cashflow
Get cash flow forecast.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?weeks=12`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "weeks": 12,
    "forecast": [
      { "week_start": "2024-01-15", "expected_inflow": 500000, "confidence": 0.8 },
      { "week_start": "2024-01-22", "expected_inflow": 750000, "confidence": 0.6 }
    ],
    "total_forecast": 4200000
  }
}
```

### GET /api/v1/dashboard/top-debtors
Get top debtors by outstanding.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?limit=10`

**Response (200):**
```json
{
  "success": true,
  "data": [
    { "customer_id": "uuid", "name": "Adani Enterprises", "outstanding": 1890000, "overdue": 1890000, "risk_level": "HIGH", "oldest_invoice_date": "2023-11-15" }
  ]
}
```

### GET /api/v1/dashboard/dso
Get DSO trend.

**Headers:** `Authorization: Bearer <jwt>`

**Query:** `?period=90d` (30d, 90d, 1y, fy)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "period": "90d",
    "current_dso": 42.5,
    "trend": [
      { "date": "2024-01-01", "dso": 45.2 },
      { "date": "2024-01-08", "dso": 43.8 }
    ]
  }
}
```

---

## SETTINGS ENDPOINTS

### GET /api/v1/settings
Get tenant settings.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "tenant": { "name": "ABC Trading Co", "subdomain": "abc-trading", "billing_plan": "professional" },
    "tally": { "sync_interval_minutes": 15, "auto_sync": true },
    "reminders": { "default_channel": "whatsapp", "business_hours_only": true, "timezone": "Asia/Kolkata" },
    "payments": { "razorpay_enabled": true, "default_link_expiry_days": 30 },
    "notifications": { "whatsapp_provider": "twilio", "email_provider": "sendgrid" }
  }
}
```

### PUT /api/v1/settings
Update tenant settings.

**Headers:** `Authorization: Bearer <jwt>`

**Request:** Partial settings object

**Response (200):** Updated settings

### GET /api/v1/users
List team members.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):** List of users with roles

### POST /api/v1/users/invite
Invite team member.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{
  "email": "colleague@abc.com",
  "role": "analyst"
}
```

**Response (201):** Created invitation

### PUT /api/v1/users/{id}/role
Update user role.

**Headers:** `Authorization: Bearer <jwt>`

**Request:**
```json
{ "role": "tenant_admin" }
```

**Response (200):** Updated user

### DELETE /api/v1/users/{id}
Remove team member.

**Headers:** `Authorization: Bearer <jwt>`

**Response (200):** `{ "success": true, "data": { "message": "User removed" } }`

---

## PUBLIC ENDPOINTS (No Auth)

### GET /pay/{token}
Public payment page for payment link.

**Response (200):** HTML page with payment form

### POST /pay/{token}/initiate
Initiate payment from public page.

**Request:**
```json
{
  "payment_method": "upi",
  "payer_name": "John Doe",
  "payer_email": "john@example.com",
  "payer_phone": "9876543210"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "razorpay_order_id": "order_xxx",
    "amount": 1180000,
    "currency": "INR"
  }
}
```

### GET /health
Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "keycloak": "healthy"
  }
}
```

---

## Rate Limits

| Endpoint Group | Limit (per tenant) |
|----------------|-------------------|
| Auth | 10 req/min |
| Agents | 30 req/min |
| Tally Sync | 5 req/min (agent), 1 req/min (manual) |
| Customers/Invoices | 100 req/min |
| Collections | 50 req/min |
| Payments | 30 req/min |
| Dashboard | 60 req/min |
| Settings | 20 req/min |
| Public Payment | 20 req/min per IP |

---

## Webhook Security

### Razorpay Webhook
- **Header**: `X-Razorpay-Signature`
- **Verification**: HMAC-SHA256 with webhook secret
- **Idempotency**: `razorpay_payment_id` unique constraint

### WhatsApp/Email/SMS Provider Callbacks
- **Validation**: Provider-specific signature verification
- **Processing**: Async via Celery worker

---

## SDK / Client Generation

```bash
# Generate TypeScript client
npx openapi-typescript-codegen -i openapi.yaml -o packages/api-client/src -c axios

# Generate Python client
pip install openapi-python-client
openapi-python-client generate --path openapi.yaml --output packages/api-client-python
```

---

## Versioning Strategy

- **Current**: `/api/v1/` (all endpoints)
- **Breaking changes**: New version `/api/v2/`
- **Deprecation**: 6-month notice, `Deprecation` header on v1
- **Sunset**: `Sunset` header with date