# CredFlow Tally Integration Specification

## Overview
This document defines the complete Tally integration: XML request/response formats, field mappings, sync mechanisms, and agent architecture.

## Tally XML API Basics

### Connection
- **Protocol**: HTTP POST
- **Endpoint**: `http://localhost:9000` (default Tally HTTP port)
- **Content-Type**: `text/xml`
- **Encoding**: UTF-8 (Tally uses UTF-16LE natively, but accepts UTF-8)

### Envelope Structure
All requests/responses wrapped in `<ENVELOPE>`:

```xml
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCURRENTCOMPANY>Company Name</SVCURRENTCOMPANY>
      </STATICVARIABLES>
      <FETCHLIST>
        <FETCH>NAME</FETCH>
        <FETCH>GUID</FETCH>
        <!-- ... more fields -->
      </FETCHLIST>
    </DESC>
  </BODY>
</ENVELOPE>
```

---

## 1. COMPANY LIST

### Request
```xml
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Companies</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <FETCHLIST>
        <FETCH>NAME</FETCH>
        <FETCH>GUID</FETCH>
        <FETCH>STATENAME</FETCH>
        <FETCH>COUNTRYNAME</FETCH>
        <FETCH>FINANCIALYEARFROM</FETCH>
        <FETCH>BOOKSFINYEARFROM</FETCH>
      </FETCHLIST>
    </DESC>
  </BODY>
</ENVELOPE>
```

### Response
```xml
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <STATUS>1</STATUS>
  </HEADER>
  <BODY>
    <DATA>
      <TALLYMESSAGE>
        <COMPANY>
          <NAME>ABC Trading Co.</NAME>
          <GUID>a1b2c3d4-e5f6-7890-abcd-ef1234567890</GUID>
          <STATENAME>Maharashtra</STATENAME>
          <COUNTRYNAME>India</COUNTRYNAME>
          <FINANCIALYEARFROM>20240401</FINANCIALYEARFROM>
          <BOOKSFINYEARFROM>20240401</BOOKSFINYEARFROM>
        </COMPANY>
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>
```

### Field Mapping
| Tally Field | DB Column | Type | Notes |
|-------------|-----------|------|-------|
| `NAME` | `name` | VARCHAR(255) | Company display name |
| `GUID` | `tally_guid` | UUID | Unique identifier, used for sync |
| `STATENAME` | `state_name` | VARCHAR(100) | State for GST |
| `COUNTRYNAME` | `country_name` | VARCHAR(100) | Usually "India" |
| `FINANCIALYEARFROM` | `financial_year_start` | DATE | Format: YYYYMMDD |
| `BOOKSFINYEARFROM` | `books_fin_year_start` | DATE | Format: YYYYMMDD |

---

## 2. LEDGERS (CUSTOMERS)

### Request
```xml
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCURRENTCOMPANY>ABC Trading Co.</SVCURRENTCOMPANY>
      </STATICVARIABLES>
      <FETCHLIST>
        <FETCH>NAME</FETCH>
        <FETCH>GUID</FETCH>
        <FETCH>PARENT</FETCH>
        <FETCH>OPENINGBALANCE</FETCH>
        <FETCH>CLOSINGBALANCE</FETCH>
        <FETCH>ADDRESS</FETCH>
        <FETCH>ADDRESS.LIST</FETCH>
        <FETCH>STATENAME</FETCH>
        <FETCH>COUNTRYNAME</FETCH>
        <FETCH>PINCODE</FETCH>
        <FETCH>LEDGERMOBILE</FETCH>
        <FETCH>LEDGEREMAIL</FETCH>
        <FETCH>PARTYGSTIN</FETCH>
        <FETCH>ISPARTYLEDGER</FETCH>
        <FETCH>ISDEEMEDPOSITIVE</FETCH>
      </FETCHLIST>
    </DESC>
  </BODY>
</ENVELOPE>
```

### Response (Customer Ledger)
```xml
<TALLYMESSAGE>
  <LEDGER NAME="Reliance Industries Ltd" RESERVEDNAME="">
    <GUID>e2f3a4b5-c6d7-8901-bcde-f23456789012</GUID>
    <PARENT>Sundry Debtors</PARENT>
    <OPENINGBALANCE>0</OPENINGBALANCE>
    <CLOSINGBALANCE>1250000.00</CLOSINGBALANCE>
    <ADDRESS>
      <ADDRESS.LIST TYPE="String">
        <ADDRESS>Maker Chambers IV, Nariman Point</ADDRESS>
        <ADDRESS>Mumbai</ADDRESS>
        <ADDRESS>Maharashtra</ADDRESS>
        <ADDRESS>400021</ADDRESS>
      </ADDRESS.LIST>
    </ADDRESS>
    <STATENAME>Maharashtra</STATENAME>
    <COUNTRYNAME>India</COUNTRYNAME>
    <PINCODE>400021</PINCODE>
    <LEDGERMOBILE>9876543210</LEDGERMOBILE>
    <LEDGEREMAIL>accounts@reliance.com</LEDGEREMAIL>
    <PARTYGSTIN>27AAACR5055K1ZP</PARTYGSTIN>
    <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  </LEDGER>
</TALLYMESSAGE>
```

### Field Mapping
| Tally Field | DB Column | Type | Transform |
|-------------|-----------|------|-----------|
| `NAME` | `name` | VARCHAR(255) | Direct |
| `GUID` | `tally_ledger_guid` | UUID | Direct |
| `PARENT` | - | - | Filter: only "Sundry Debtors" children |
| `CLOSINGBALANCE` | `outstanding_amount` | DECIMAL(15,2) | Parse float |
| `ADDRESS.LIST` | `address` | JSONB | Array → `{line1, city, state, pincode}` |
| `STATENAME` | `state` | VARCHAR(100) | Direct |
| `COUNTRYNAME` | `country` | VARCHAR(100) | Direct |
| `PINCODE` | `pincode` | VARCHAR(10) | Direct |
| `LEDGERMOBILE` | `phone` | VARCHAR(20) | Direct |
| `LEDGEREMAIL` | `email` | VARCHAR(255) | Direct |
| `PARTYGSTIN` | `gstin` | VARCHAR(15) | Uppercase, validate format |
| `ISPARTYLEDGER` | - | - | Must be "Yes" for customers |
| `ISDEEMEDPOSITIVE` | - | - | Must be "Yes" for debtors |

### Filtering Logic
- Only process ledgers where `PARENT` = "Sundry Debtors" (or configured receivables group)
- And `ISPARTYLEDGER` = "Yes"
- And `ISDEEMEDPOSITIVE` = "Yes"
- Skip: Groups, Bank accounts, Tax ledgers, Expense/Income ledgers

---

## 3. SALES VOUCHERS (INVOICES)

### Request
```xml
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>Day Book</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCURRENTCOMPANY>ABC Trading Co.</SVCURRENTCOMPANY>
        <SVFROMDATE>20240401</SVFROMDATE>
        <SVTODATE>20250331</SVTODATE>
        <EXPLODEVOUCHERS>Yes</EXPLODEVOUCHERS>
        <EXPLODEBATCHALLOCATIONS>Yes</EXPLODEBATCHALLOCATIONS>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <REPORT NAME="Day Book" ISMODIFY="Yes">
            <LOCAL>Collection : Default : Add :Filter : VchTypeFilter</LOCAL>
            <LOCAL>Collection : Default : Add :Fetch : VoucherTypeName</LOCAL>
            <LOCAL>Collection : Default : Add :Fetch : VoucherNumber</LOCAL>
            <LOCAL>Collection : Default : Add :Fetch : Date</LOCAL>
            <LOCAL>Collection : Default : Add :Fetch : EffectiveDate</LOCAL>
            <LOCAL>Collection : Default : Add :Fetch : Narration</LOCAL>
            <LOCAL>Collection : Default : Add :Fetch : PartyLedgerName</LOCAL>
            <LOCAL>Collection : Default :Fetch : PartyName</LOCAL>
            <LOCAL>Collection : Default :Fetch : Amount</LOCAL>
            <LOCAL>Collection : Default :Fetch : LedgerEntriesList</LOCAL>
            <LOCAL>Collection : Default :Fetch : InventoryEntriesList</LOCAL>
            <LOCAL>Collection : Default :Fetch : AccountingAllocationsList</LOCAL>
            <LOCAL>Collection : Default :Fetch : BillAllocationsList</LOCAL>
          </REPORT>
          <SYSTEM TYPE="Formulae" NAME="VchTypeFilter">
            $VoucherTypeName="Sales" OR $VoucherTypeName="Sales - GST"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
```

### Response (Sales Voucher)
```xml
<TALLYMESSAGE>
  <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Accounting Voucher View">
    <DATE>20240415</DATE>
    <EFFECTIVEDATE>20240415</EFFECTIVEDATE>
    <VOUCHERNUMBER>1</VOUCHERNUMBER>
    <NARRATION>Sales Invoice - Reliance Industries</NARRATION>
    <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
    <PARTYLEDGERNAME>Reliance Industries Ltd</PARTYLEDGERNAME>
    <PARTYNAME>Reliance Industries Ltd</PARTYNAME>
    <AMOUNT>-1180000.00</AMOUNT>
    <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>Reliance Industries Ltd</LEDGERNAME>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
      <ISLASTDEEMEDPOSITIVE>Yes</ISLASTDEEMEDPOSITIVE>
      <AMOUNT>-1180000.00</AMOUNT>
      <BILLALLOCATIONS.LIST>
        <NAME>INV-2024-001</NAME>
        <BILLTYPE>New Ref</BILLTYPE>
        <AMOUNT>-1180000.00</AMOUNT>
      </BILLALLOCATIONS.LIST>
    </ALLLEDGERENTRIES.LIST>
    <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>Sales - GST 18%</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <AMOUNT>1000000.00</AMOUNT>
      <ACCOUNTINGALLOCATIONS.LIST>
        <LEDGERNAME>Sales - GST 18%</LEDGERNAME>
        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
        <AMOUNT>1000000.00</AMOUNT>
      </ACCOUNTINGALLOCATIONS.LIST>
    </ALLLEDGERENTRIES.LIST>
    <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>CGST Output 9%</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <AMOUNT>90000.00</AMOUNT>
    </ALLLEDGERENTRIES.LIST>
    <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>SGST Output 9%</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <AMOUNT>90000.00</AMOUNT>
    </ALLLEDGERENTRIES.LIST>
  </VOUCHER>
</TALLYMESSAGE>
```

### Field Mapping
| Tally Field | DB Column | Type | Transform |
|-------------|-----------|------|-----------|
| `VOUCHERNUMBER` | `voucher_number` | VARCHAR(100) | Direct |
| `DATE` | `voucher_date` | DATE | Parse YYYYMMDD |
| `EFFECTIVEDATE` | `due_date` | DATE | Parse YYYYMMDD (or voucher_date + terms) |
| `VOUCHERTYPENAME` | - | - | Filter: Sales types only |
| `PARTYLEDGERNAME` | - | - | Match to customer `tally_ledger_guid` |
| `AMOUNT` (voucher level) | `total_amount` | DECIMAL(15,2) | Absolute value |
| `ALLLEDGERENTRIES.LIST[Party]` → `AMOUNT` | `outstanding_amount` | DECIMAL(15,2) | Absolute value (negative in Tally = debit) |
| `ALLLEDGERENTRIES.LIST[Party]` → `BILLALLOCATIONS.LIST.NAME` | `tally_voucher_id` | VARCHAR(100) | Bill reference = unique voucher ID |
| `ALLLEDGERENTRIES.LIST[Sales]` → `AMOUNT` | `amount` | DECIMAL(15,2) | Taxable amount |
| `ALLLEDGERENTRIES.LIST[CGST]` → `AMOUNT` | `cgst_amount` | DECIMAL(15,2) | Tax component |
| `ALLLEDGERENTRIES.LIST[SGST]` → `AMOUNT` | `sgst_amount` | DECIMAL(15,2) | Tax component |
| `ALLLEDGERENTRIES.LIST[IGST]` → `AMOUNT` | `igst_amount` | DECIMAL(15,2) | Tax component (inter-state) |
| `NARRATION` | `narration` | TEXT | Direct |

### Amount Calculation Logic
```python
# Tally uses negative for debit (customer), positive for credit (sales/tax)
# Invoice total = abs(party_ledger_amount)
# Taxable amount = sales_ledger_amount
# CGST = cgst_ledger_amount
# SGST = sgst_ledger_amount
# IGST = igst_ledger_amount (if inter-state)

tax_amount = cgst + sgst + igst
total_amount = taxable_amount + tax_amount
outstanding_amount = total_amount  # Initially, reduced by payments
```

---

## 4. RECEIPT VOUCHERS (PAYMENTS)

### Request
Same as Sales Vouchers but filter: `$VoucherTypeName="Receipt"`

### Response (Receipt Voucher)
```xml
<TALLYMESSAGE>
  <VOUCHER VCHTYPE="Receipt" ACTION="Create" OBJVIEW="Accounting Voucher View">
    <DATE>20240515</DATE>
    <EFFECTIVEDATE>20240515</EFFECTIVEDATE>
    <VOUCHERNUMBER>1</VOUCHERNUMBER>
    <NARRATION>Payment received from Reliance - INV-2024-001</NARRATION>
    <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
    <PARTYLEDGERNAME>Reliance Industries Ltd</PARTYLEDGERNAME>
    <AMOUNT>1180000.00</AMOUNT>
    <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>HDFC Bank Ltd</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <AMOUNT>1180000.00</AMOUNT>
    </ALLLEDGERENTRIES.LIST>
    <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>Reliance Industries Ltd</LEDGERNAME>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
      <AMOUNT>-1180000.00</AMOUNT>
      <BILLALLOCATIONS.LIST>
        <NAME>INV-2024-001</NAME>
        <BILLTYPE>Agst Ref</BILLTYPE>
        <AMOUNT>-1180000.00</AMOUNT>
      </BILLALLOCATIONS.LIST>
    </ALLLEDGERENTRIES.LIST>
  </VOUCHER>
</TALLYMESSAGE>
```

### Field Mapping
| Tally Field | DB Column | Type | Transform |
|-------------|-----------|------|-----------|
| `VOUCHERNUMBER` | `reference_number` | VARCHAR(100) | Direct |
| `DATE` | `payment_date` | DATE | Parse YYYYMMDD |
| `PARTYLEDGERNAME` | - | - | Match to customer |
| `AMOUNT` (voucher level) | `amount` | DECIMAL(15,2) | Absolute value |
| `ALLLEDGERENTRIES.LIST[Bank]` → `AMOUNT` | - | - | Bank side (credit) |
| `ALLLEDGERENTRIES.LIST[Party]` → `AMOUNT` | - | - | Party side (debit, negative) |
| `ALLLEDGERENTRIES.LIST[Party]` → `BILLALLOCATIONS.LIST.NAME` | - | - | Matches invoice `tally_voucher_id` |
| `ALLLEDGERENTRIES.LIST[Party]` → `BILLALLOCATIONS.LIST.BILLTYPE` | - | - | "Agst Ref" = against reference |

### Payment Matching Logic
```python
# 1. Find customer by PARTYLEDGERNAME (match tally_ledger_guid)
# 2. Find invoice by BILLALLOCATIONS.LIST.NAME (match tally_voucher_id)
# 3. If exact match: link payment to invoice
# 4. If partial: create payment, reduce invoice outstanding_amount
# 5. If no invoice match: create unallocated payment (customer credit)
```

---

## DATA TYPE CONVERSIONS

| Tally Format | Target Type | Conversion |
|--------------|-------------|------------|
| `20240415` (YYYYMMDD) | DATE | `datetime.strptime(val, "%Y%m%d").date()` |
| `-1180000.00` | DECIMAL(15,2) | `abs(Decimal(val))` |
| `Yes`/`No` | BOOLEAN | `val.lower() == "yes"` |
| `1250000.00` | DECIMAL(15,2) | `Decimal(val)` |
| `27AAACR5055K1ZP` | VARCHAR(15) | `val.upper().strip()` |
| `a1b2c3d4-e5f6-7890-abcd-ef1234567890` | UUID | Direct (validate format) |

---

## SYNC MECHANISM

### Delta Sync Strategy
1. **Track per-entity cursors**: `last_sync_timestamp` per (company, entity_type)
2. **Request only changes**: Tally supports `SVFROMDATE`/`SVTODATE` for date-range filtering
3. **Upsert logic**: Use `tally_ledger_guid` (customers) and `tally_voucher_id` (invoices) as unique keys

### Sync Payload (Agent → Cloud)
```json
{
  "company_id": "tally_company_guid",
  "synced_at": "2024-01-15T10:00:00Z",
  "customers": [
    {
      "tally_ledger_guid": "guid",
      "name": "Reliance Industries Ltd",
      "gstin": "27AAACR5055K1ZP",
      "address": {"line1": "...", "city": "Mumbai", "state": "Maharashtra", "pincode": "400021"},
      "contact_person": "John Doe",
      "phone": "9876543210",
      "email": "accounts@reliance.com",
      "credit_limit": 1000000,
      "payment_terms_days": 30
    }
  ],
  "invoices": [
    {
      "tally_voucher_id": "INV-2024-001",
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
      "invoice_tally_voucher_id": "INV-2024-001",
      "customer_tally_guid": "customer_guid",
      "amount": 1180000,
      "payment_date": "2024-02-10",
      "payment_mode": "bank_transfer",
      "reference_number": "UTIB123456"
    }
  ]
}
```

### Sync Processing (Cloud)
1. Validate payload schema
2. For each customer: `upsert` on `(tenant_id, tally_ledger_guid)`
3. For each invoice: `upsert` on `(tenant_id, tally_voucher_id)`
4. For each payment: `upsert` on `(tenant_id, tally_receipt_id)`
5. Link payments to invoices via `tally_voucher_id` → `BILLALLOCATIONS.LIST.NAME`
6. Update `tally_companies.last_synced_at`
7. Create `sync_log` record

### Upsert Logic
```sql
-- Customers
INSERT INTO customers (tenant_id, tally_ledger_guid, name, gstin, ...)
VALUES (...)
ON CONFLICT (tenant_id, tally_ledger_guid) DO UPDATE SET
  name = EXCLUDED.name,
  gstin = EXCLUDED.gstin,
  address = EXCLUDED.address,
  updated_at = NOW();

-- Invoices
INSERT INTO invoices (tenant_id, customer_id, tally_voucher_id, voucher_number, ...)
VALUES (...)
ON CONFLICT (tenant_id, tally_voucher_id) DO UPDATE SET
  customer_id = EXCLUDED.customer_id,
  voucher_number = EXCLUDED.voucher_number,
  due_date = EXCLUDED.due_date,
  total_amount = EXCLUDED.total_amount,
  outstanding_amount = EXCLUDED.total_amount - COALESCE((
    SELECT SUM(amount) FROM payments WHERE invoice_id = invoices.id
  ), 0),
  updated_at = NOW();
```

---

## AGENT ARCHITECTURE (Go)

### Components
```
tally-agent/
├── main.go              # Entry point, Windows service setup
├── config/
│   └── config.go        # YAML config parsing
├── tally/
│   ├── client.go        # HTTP client for Tally XML API
│   ├── requests.go      # XML request builders
│   ├── responses.go     # XML response parsers
│   └── mappings.go      # Field mapping logic
├── queue/
│   └── sqlite.go        # Local SQLite queue (WAL mode)
├── upload/
│   └── uploader.go      # HTTPS upload with retry
├── health/
│   └── reporter.go      # Heartbeat to cloud
├── updater/
│   └── updater.go       # GitHub Releases auto-update
└── service/
    └── windows.go       # Windows Service wrapper
```

### Config (config.yaml)
```yaml
tally:
  url: "http://localhost:9000"
  company: "ABC Trading Co."
  
cloud:
  api_url: "https://api.credflow.in"
  api_key: "cf_abc123..."  # Set during registration
  
sync:
  interval_minutes: 15
  entity_types: ["companies", "customers", "invoices", "payments"]
  max_payload_mb: 50
  
queue:
  path: "C:/ProgramData/CredFlow/queue.db"
  max_age_days: 7
  
health:
  heartbeat_interval_minutes: 5
  
updater:
  check_interval_hours: 24
  github_repo: "credflow/tally-agent"
```

### Local SQLite Queue Schema
```sql
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,        -- customers, invoices, payments
    payload_json TEXT NOT NULL,       -- JSON payload
    company_guid TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    last_attempt_at DATETIME,
    status TEXT DEFAULT 'pending'     -- pending, processing, completed, failed
);

CREATE INDEX idx_sync_queue_status ON sync_queue(status);
CREATE INDEX idx_sync_queue_entity ON sync_queue(entity_type);
```

### Retry Logic
```go
// Exponential backoff with jitter
func backoff(attempt int) time.Duration {
    base := time.Minute * time.Duration(1<<attempt) // 1m, 2m, 4m, 8m, 16m, 32m, 1h max
    jitter := time.Duration(rand.Int63n(int64(base / 4)))
    return base + jitter
}

// Max retry: 7 attempts (1h max backoff)
// After max retries: move to dead letter, alert via sync_log
```

### Windows Service
- Uses `golang.org/x/sys/windows/svc`
- Auto-start: `svc.Config{StartType: svc.StartAutomatic}`
- Recovery: Restart after 30s, max 3 failures, then reboot
- Event Log: Source "CredFlowAgent", log Application events

### Auto-Updater
```go
// On startup:
// 1. Fetch latest release from GitHub API
// 2. Compare version with current
// 3. Download new binary to temp
// 4. Verify checksum
// 5. Replace current binary (Windows: rename + move)
// 6. Restart service
```

---

## ERROR HANDLING

### Tally Connection Errors
| Error | Agent Behavior |
|-------|----------------|
| Connection refused | Retry with backoff, log, continue |
| Tally not running | Skip cycle, log warning |
| XML parse error | Log error, skip entity, continue |
| HTTP 5xx | Retry with backoff |

### Cloud Upload Errors
| Error | Agent Behavior |
|-------|----------------|
| 401 Unauthorized | Refresh API key (if rotation), re-register |
| 429 Rate Limited | Respect Retry-After header |
| 5xx Server Error | Retry with backoff |
| Network timeout | Retry with backoff |

### Data Quality Issues
| Issue | Handling |
|-------|----------|
| Missing GSTIN | Log warning, import with null GSTIN |
| Invalid date | Use voucher date, log warning |
| Duplicate voucher | Upsert handles (idempotent) |
| Customer not found for invoice | Create "Unknown Customer", flag for review |
| Amount mismatch | Log error, skip invoice, alert |

---

## TESTING

### Mock Tally Server
- Flask app serving static XML responses
- Endpoints: `/` (accepts any POST, returns appropriate response based on request)
- Used for: Unit tests, integration tests, CI/CD

### Test Cases
1. **Full sync**: Companies → Customers → Invoices → Payments
2. **Delta sync**: Only new/modified records since last sync
3. **Partial payment**: Payment < invoice amount
4. **Overpayment**: Payment > invoice amount
5. **Inter-state invoice**: IGST instead of CGST+SGST
6. **Customer update**: Address/GSTIN change in Tally
7. **Invoice cancellation**: Status change in Tally
8. **Network failure**: Queue persists, retries on recovery

---

## MONITORING & ALERTING

### Metrics
- `tally_sync_duration_seconds` (histogram)
- `tally_sync_records_processed` (counter)
- `tally_sync_errors_total` (counter by error_type)
- `agent_heartbeat_lag_seconds` (gauge)
- `sync_queue_depth` (gauge)

### Alerts
- Agent offline > 15 min → PagerDuty
- Sync failed 3x consecutive → PagerDuty
- Queue depth > 1000 → Warning
- Sync lag > 2 hours → Warning