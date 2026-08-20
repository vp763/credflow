# ADR-006: Message Queue - Redis Streams + Celery

## Context
CredFlow needs background job processing for:
- Tally sync data processing (heavy XML parsing, upserts)
- WhatsApp/Email/SMS reminder sending
- Payment webhook processing (Razorpay)
- Analytics computation (aging, DSO, cash flow forecast)
- Report generation
- Scheduled tasks (Celery Beat)
- Scale from 100 to 10,000+ tenants

Requirements:
- Local dev parity with production
- Zero-code-change migration to Azure
- Reliable delivery with retries
- Priority queues for time-sensitive jobs
- Visibility/monitoring

## Decision
Use **Redis Streams** as the message broker with **Celery** for task orchestration.

### Queue Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    Redis Streams                             │
├─────────────────────────────────────────────────────────────┤
│  Queue: default      │ General tasks, API background work   │
│  Queue: tally        │ Tally sync processing (high volume)  │
│  Queue: sync         │ Data sync, upsert operations         │
│  Queue: notifications│ WhatsApp, Email, SMS sending         │
│  Queue: payments     │ Payment webhooks, reconciliation     │
│  Queue: analytics    │ Aging, DSO, cash flow, reports       │
└─────────────────────────────────────────────────────────────┘
```

### Celery Configuration
```python
# Local (docker-compose)
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"

# Azure Production
CELERY_BROKER_URL = "rediss://:password@credflow-redis.redis.cache.windows.net:6380/0"
CELERY_RESULT_BACKEND = "rediss://:password@credflow-redis.redis.cache.windows.net:6380/0"
```

### Worker Deployment
- **API container**: Runs FastAPI only (no Celery worker)
- **Worker container**: `celery -A app.worker worker -Q default,tally,sync,notifications,payments -c 4`
- **Scheduler container**: `celery -A app.worker beat` (single instance)

### Job Definitions
| Job | Queue | Trigger | Timeout | Retries | Backoff |
|-----|-------|---------|---------|---------|---------|
| `process_tally_sync` | tally | API (sync endpoint) | 300s | 3 | exponential |
| `send_whatsapp` | notifications | Reminder engine | 30s | 5 | exponential |
| `send_email` | notifications | Reminder engine | 30s | 5 | exponential |
| `process_razorpay_webhook` | payments | Webhook | 60s | 3 | linear |
| `compute_aging_buckets` | analytics | Schedule (hourly) | 120s | 2 | exponential |
| `compute_dso` | analytics | Schedule (daily) | 180s | 2 | exponential |
| `generate_daily_report` | analytics | Schedule (daily) | 300s | 1 | - |

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **RabbitMQ** | Mature, AMQP, dead letter queues, priority queues | Extra infrastructure, doesn't map 1:1 to Azure Service Bus |
| **Azure Service Bus (native)** | Cloud-native, sessions, transactions | No local emulator parity, vendor lock-in |
| **Redis Streams + Celery** | Simple, local=prod parity, Celery abstraction, maps to Azure Cache for Redis | Fewer advanced features (no native DLQ, but Celery handles retries) |
| **Database polling (pg_notify)** | No extra infra | Not scalable, polling overhead |

## Consequences

**Positive:**
- **Zero code change** for local→Azure: only `CELERY_BROKER_URL` env var changes
- **Local dev parity**: Same Redis image locally and in Azure (Azure Cache for Redis)
- **Celery abstraction**: Task definitions unchanged, broker is implementation detail
- **Priority via queue routing**: Critical jobs (payments) on dedicated queue with more workers
- **Built-in retries/backoff**: Celery handles retry logic declaratively
- **Monitoring**: Flower for Celery monitoring, Redis INFO for queue depth
- **Cost-effective**: Single Redis instance for cache + queue

**Negative:**
- Redis Streams lacks native dead-letter queues (Celery retries + manual DLQ table)
- No message TTL at stream level (Celery handles expiration)
- Single Redis instance = single point of failure (mitigated: Azure Cache for Redis has HA)

## Implementation Notes
- Redis config: `maxmemory 256mb`, `maxmemory-policy allkeys-lru` (local), Azure uses dedicated tier
- Celery serializer: JSON (secure, interoperable)
- Task routing: `@app.task(queue='tally')` decorator
- Result backend: Redis (short-lived results, 24h TTL)
- Beat schedule: Defined in `celery_app.conf.beat_schedule` (persistent in Redis)
- Monitoring: Flower dashboard on port 5555 (dev only)
- Health check: `celery -A app.worker inspect ping` in Docker healthcheck