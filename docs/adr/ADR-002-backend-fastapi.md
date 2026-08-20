# ADR-002: Backend Framework - FastAPI (Python)

## Context
CredFlow backend requires:
- RESTful API with OpenAPI 3.0 spec generation
- Async database operations (PostgreSQL with asyncpg)
- Background job processing (Celery with Redis)
- Multi-tenant isolation (JWT → Middleware → ORM → RLS)
- Tally XML parsing and sync processing
- Webhook handling (Razorpay, WhatsApp providers)
- High performance for 100→10,000 tenants
- Team has Python expertise

## Decision
Use **FastAPI** with Python 3.11+ as the backend framework with:
- **SQLAlchemy 2.0** (async) + **Alembic** for ORM/migrations
- **Pydantic v2** for validation and settings
- **Celery** + **Redis Streams** for background jobs
- **uv** for package management (faster than pip)
- **uvicorn** + **gunicorn** for production ASGI server

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **NestJS (TypeScript)** | Type-safe full stack, familiar to FE team, decorators | ORM options less mature (TypeORM/Prisma), heavier runtime |
| **Go (Gin/Fiber)** | Fast, single binary, great concurrency | Team less experienced, no native async ORM, more verbose |
| **Hono (TypeScript)** | Fast, lightweight, edge-ready | Ecosystem smaller, less battle-tested for complex SaaS |
| **FastAPI (Python)** | Excellent async support, auto OpenAPI, great SQLAlchemy, rich ecosystem | Python GIL (mitigated by workers), slower raw throughput than Go |

## Consequences

**Positive:**
- Automatic OpenAPI 3.0 spec generation from code
- Native async/await with SQLAlchemy 2.0 asyncpg
- Pydantic v2 for fast validation and settings management
- Rich ecosystem for Tally XML parsing (lxml, xmltodict)
- Celery is mature and well-integrated with FastAPI
- Team has Python expertise
- Easy to add background workers, schedulers
- Type hints + mypy for static analysis

**Negative:**
- Python GIL limits CPU-bound concurrency (mitigated by multiple workers)
- Deployment requires Python runtime (vs single binary Go)
- Need separate process for Celery workers

## Implementation Notes
- Package management with `uv` (10-100x faster than pip)
- Multi-stage Dockerfile: dev (with uv sync --all-extras) and prod (uv sync --no-dev)
- Settings via `pydantic-settings` with `.env` support
- Structured logging with `structlog` + JSON output
- OpenTelemetry instrumentation for tracing/metrics
- Celery app shared across `api`, `worker`, `scheduler` containers
- Health check endpoint at `/health` for container orchestration