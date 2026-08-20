# ADR-001: Monorepo Structure - Turborepo

## Context
We need a monorepo structure to manage multiple packages and applications for CredFlow (Tally integration SaaS for Indian SMEs). The monorepo must support:
- Multiple deployable applications (frontend, backend API, worker, scheduler)
- Shared packages (types, config, database, API client, UI components, domain packages)
- Independent build/deploy of each app
- Shared TypeScript configuration and path aliases
- Efficient caching and parallel execution

## Decision
Use **Turborepo** as the monorepo tool with the following structure:

```
credflow/
├── apps/
│   ├── web/              # Next.js 14 frontend
│   ├── api/              # FastAPI backend
│   ├── worker/           # Celery worker (shared with api)
│   └── scheduler/        # Celery beat scheduler (shared with api)
├── packages/
│   ├── shared/           # Shared types, utilities, constants
│   ├── config/           # Shared ESLint, Prettier, TSConfig
│   ├── db/               # Database schema, migrations, ORM models
│   ├── api-client/       # Type-safe API client (generated from OpenAPI)
│   ├── ui/               # Shared React components (shadcn/ui based)
│   ├── identity/         # Auth domain package
│   ├── tally/            # Tally integration domain
│   ├── receivables/      # Receivables domain
│   ├── collections/      # Collections/reminders domain
│   ├── payments/         # Payments domain
│   ├── analytics/        # Analytics domain
│   └── notifications/    # Notifications domain
├── docker-compose.yml
├── turbo.json
├── tsconfig.base.json
└── package.json
```

Path aliases configured in `tsconfig.base.json` for all packages.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Nx** | Powerful, built-in generators, excellent Angular/React support | Heavier, steeper learning curve, more opinionated |
| **Turborepo** | Lightweight, fast caching, simple config, Vercel-backed | Fewer built-in generators, less IDE integration |
| **Plain npm workspaces** | Zero config, native | No caching, no pipeline orchestration, no remote caching |

## Consequences

**Positive:**
- Fast builds with intelligent caching (local + remote via Vercel)
- Simple configuration (`turbo.json` + `package.json` workspaces)
- Independent deployment of apps
- Clear package boundaries aligned with DDD bounded contexts
- Shared TypeScript config ensures type safety across packages

**Negative:**
- Fewer code generators than Nx (manual package creation)
- Remote caching requires Vercel account (optional)
- Team needs to learn Turborepo conventions

## Implementation Notes
- `turbo.json` defines pipeline: build, dev, lint, typecheck, test, db:migrate, db:seed
- `tsconfig.base.json` defines path aliases for all `@credflow/*` packages
- Each package has its own `package.json`, `tsconfig.json` extending base
- Apps use `packages/*` as dependencies via workspace protocol
- GitHub Actions will run `turbo run build lint typecheck test` on PRs