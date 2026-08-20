# CredVault / CredFlow - Agent Instructions

## Current Repository State

**This is an empty Turborepo scaffold** - no apps or packages implemented yet. Only config files and mock Tally XML test data exist.

### Key Discrepancy
- **PROJECT_PLAN.md** describes **CredVault** (password manager)
- **Conversation context** describes **CredFlow** (Tally integration SaaS for Indian SMEs)
- The repo name is `CredVault` but the intended product per conversation is **CredFlow**
- Decide which product this repo serves before implementing

---

## Commands

```bash
# Install dependencies
npm install

# Run all dev servers (when apps exist)
npm run dev

# Build all packages
npm run build

# Lint all packages
npm run lint

# Typecheck all packages
npm run typecheck

# Run tests
npm run test

# Database (when db package exists)
npm run db:migrate
npm run db:seed

# Docker (when docker-compose.yml exists)
npm run docker:up
npm run docker:down
npm run docker:logs
```

---

## Monorepo Structure (Planned)

```
apps/           # Deployable applications (none yet)
packages/       # Shared libraries (none yet)
  @credflow/shared
  @credflow/config
  @credflow/db
  @credflow/api-client
  @credflow/ui
  @credflow/identity
  @credflow/tally
  @credflow/receivables
  @credflow/collections
  @credflow/payments
  @credflow/analytics
  @credflow/notifications
```

Path aliases configured in `tsconfig.base.json` for all above.

---

## Test Data: Tally XML

Located in `apps/mock-tally/data/` - sample request/response XML for:
- Company list (`request_company_list.xml`, `response_company_list.xml`)
- Ledgers/Customers (`request_ledgers.xml`, `response_ledgers.xml`)
- Sales Vouchers/Invoices (`request_sales_vouchers.xml` - response not yet created)
- Receipt Vouchers/Payments (not yet created)

Use these for mock server and parser development.

---

## Tech Stack (from PROJECT_PLAN.md - CredVault)

| Layer | Technology |
|-------|-----------|
| Monorepo | Turborepo |
| Language | TypeScript |
| Frontend | React + Vite / Next.js |
| Mobile | React Native (Expo) |
| Desktop | Tauri |
| Extension | Plasmo / WXT |
| Backend | Hono / Hapi / tRPC |
| Database | PostgreSQL (prod), SQLite (local) |
| ORM | Drizzle / Prisma |
| Auth | Better Auth / Lucia |
| Encryption | libsodium / Web Crypto |

**Note**: If building CredFlow (Tally SaaS), stack will differ - see conversation context for Azure, FastAPI, Celery, Redis, Azurite, Keycloak.

---

## Immediate Next Steps

1. **Decide product**: CredVault (password manager) vs CredFlow (Tally SaaS)
2. **Initialize first package**: Likely `packages/db` or `packages/shared`
3. **Add docker-compose.yml** for local infra (Postgres, Redis, etc.)
4. **Create first app**: `apps/api` or `apps/web`
5. **Set up CI/CD** (GitHub Actions)

---

## Git Workflow

- Use conventional commits (`feat:`, `fix:`, `chore:`, etc.)
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`
- PR required for all changes to main