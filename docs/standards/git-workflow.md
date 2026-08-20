# Git Workflow & Standards

## Branching Strategy

### Branch Types
| Prefix | Purpose | Base | Merge Target |
|--------|---------|------|--------------|
| `main` | Production-ready | — | — |
| `develop` | Integration branch | `main` | `main` (via PR) |
| `feat/<scope>` | New feature | `develop` | `develop` |
| `fix/<scope>` | Bug fix | `develop` | `develop` |
| `chore/<scope>` | Maintenance | `develop` | `develop` |
| `docs/<scope>` | Documentation | `develop` | `develop` |
| `refactor/<scope>` | Code restructuring | `develop` | `develop` |
| `release/v<X.Y.Z>` | Release prep | `develop` | `main` + `develop` |
| `hotfix/<scope>` | Production fix | `main` | `main` + `develop` |

### Branch Naming Examples
```
feat/auth-oidc
feat/tally-sync-endpoint
feat/customer-crud
fix/aging-calculation-off-by-one
fix/webhook-idempotency
chore/update-dependencies
docs/api-spec-update
refactor/tenant-middleware
release/v1.0.0
hotfix/payment-link-expiry
```

---

## Commit Messages (Conventional Commits)

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Maintenance, deps, config |
| `docs` | Documentation only |
| `refactor` | Code restructuring (no behavior change) |
| `style` | Formatting, linting |
| `test` | Adding/updating tests |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `build` | Build system changes |
| `revert` | Revert previous commit |

### Scopes
`auth`, `tally`, `customers`, `invoices`, `payments`, `collections`, `dashboard`, `settings`, `agents`, `sync`, `notifications`, `database`, `infra`, `ui`, `api`, `worker`, `scheduler`

### Examples
```
feat(auth): add Keycloak OIDC login flow

Implements authorization code flow with PKCE.
Adds /callback endpoint for token exchange.
Updates middleware to validate Keycloak tokens.

Closes #42
```

```
fix(tally): handle missing GSTIN in customer ledger

Some Tally ledgers don't have PARTYGSTIN field.
Now defaults to null instead of crashing parser.
Adds validation warning to sync log.

Fixes #156
```

```
chore(deps): upgrade FastAPI to 0.109.0

Updates pydantic to 2.5.3, sqlalchemy to 2.0.25.
Runs test suite - all pass.
```

```
refactor(database): extract base model with tenant_id

Moves tenant_id, created_at, updated_at, deleted_at
to TenantMixin. All models now inherit.
Reduces duplication across 18 models.
```

---

## Pull Request Process

### PR Requirements
- [ ] Title follows conventional commit format: `feat(auth): add OIDC login`
- [ ] Description includes: **What**, **Why**, **How to test**
- [ ] Linked to GitHub Issue (`Closes #123` or `Refs #123`)
- [ ] All CI checks pass: `lint`, `typecheck`, `test`, `build`
- [ ] At least 1 approval (2 for `main`/`release` branches)
- [ ] No merge conflicts
- [ ] Branch up to date with `develop`

### PR Template
```markdown
## Summary
Brief description of changes.

## Related Issue
Closes #<issue_number>

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing: <steps>

## Screenshots (if UI)
<attach>

## Checklist
- [ ] Code follows style guide
- [ ] Self-reviewed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Guidelines
| Reviewer | Focus |
|----------|-------|
| **Backend** | API design, SQL queries, security, performance, error handling |
| **Frontend** | UX, accessibility, TypeScript types, component reuse, responsive |
| **Database** | Schema, indexes, migrations, RLS, query plans |
| **DevOps** | Docker, CI/CD, secrets, monitoring, scaling |
| **Architect** | Cross-cutting concerns, ADR compliance, patterns |

---

## Release Process

### Versioning (Semantic Versioning)
```
MAJOR.MINOR.PATCH
```
- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Flow
```
develop → release/v1.2.0 → main (tag v1.2.0) → develop (merge back)
                    ↓
              Hotfixes on release branch
```

### Release Checklist
- [ ] All sprint issues closed
- [ ] CHANGELOG.md updated (auto-generated from conventional commits)
- [ ] Version bumped in `package.json` + `pyproject.toml`
- [ ] Release branch created: `release/v<version>`
- [ ] Final QA on staging
- [ ] PR: `release/v<version>` → `main` (requires 2 approvals)
- [ ] Tag pushed: `git tag v1.2.0 && git push origin v1.2.0`
- [ ] GitHub Release created with notes
- [ ] PR: `release/v<version>` → `develop` (merge back)
- [ ] Deploy to production (manual approval)

### Hotfix Process
```
main → hotfix/<issue> → main (tag v1.2.1) → develop (merge back)
```

---

## Code Standards

### Python (Backend)
```toml
# Enforced via ruff + black + mypy + isort
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM", "ARG", "PTH", "ERA", "PL", "TRY"]

[tool.black]
line-length = 100

[tool.mypy]
strict = true
disallow_untyped_defs = true
```

**Key Rules:**
- Type hints required on all public functions
- Async/await for all I/O
- Structured logging with `structlog`
- Pydantic models for request/response
- SQLAlchemy 2.0 style (select/async)
- Custom exceptions with error codes

### TypeScript (Frontend)
```json
// Enforced via eslint + prettier + tsc
{
  "strict": true,
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true
}
```

**Key Rules:**
- Functional components + hooks
- TanStack Query for server state
- React Hook Form + Zod for forms
- shadcn/ui components (copy-paste ownership)
- CSS variables for theming
- No `any` type (use `unknown`)

### Database
- All tables: `id` (UUID), `tenant_id` (UUID FK), `created_at`, `updated_at`, `deleted_at`
- ENUMs for fixed value sets
- JSONB for flexible data
- Indexes based on query patterns (not guesses)
- Partitioning for high-volume tables
- RLS policies on all tenant tables
- Migrations: descriptive names, reversible

---

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run lint
  
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run typecheck
  
  test:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:16 }
      redis: { image: redis:7 }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: uv sync --all-extras
      - run: uv run pytest --cov=app --cov-fail-under=70
  
  build:
    needs: [lint, typecheck, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
      - run: docker build -t credflow/backend:${{ github.sha }} ./apps/backend
      - run: docker push credflow/backend:${{ github.sha }}
```

### Required Checks (Branch Protection)
- `lint`
- `typecheck`
- `test`
- `build`

---

## Development Workflow

### Local Setup
```bash
# 1. Clone
git clone https://github.com/credflow/credflow.git
cd credflow

# 2. Install deps
npm install

# 3. Start infrastructure
npm run docker:up

# 4. Run migrations
npm run db:migrate

# 5. Start dev servers
npm run dev
```

### Feature Workflow
```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feat/customer-search

# 3. Work in small commits
git add -A
git commit -m "feat(customers): add search by name and GSTIN"
git commit -m "test(customers): add search integration tests"

# 4. Push and create PR
git push origin feat/customer-search
# Create PR via GitHub UI

# 5. After approval + CI pass
# Squash and merge via GitHub UI

# 6. Clean up
git checkout develop
git pull origin develop
git branch -d feat/customer-search
```

### Hotfix Workflow
```bash
# 1. From main
git checkout main
git pull origin main

# 2. Create hotfix branch
git checkout -b hotfix/payment-link-expiry

# 3. Fix + test
git commit -m "fix(payments): extend payment link default expiry to 30 days"

# 4. PR to main (2 approvals required)
# Merge to main → auto-tag

# 5. Merge back to develop
git checkout develop
git merge main
git push origin develop
```

---

## Code Review Checklist

### Backend
- [ ] No `print()` statements (use `logger`)
- [ ] No raw SQL (use SQLAlchemy)
- [ ] No hardcoded secrets
- [ ] Error codes follow convention
- [ ] Pagination on list endpoints
- [ ] Rate limiting considered
- [ ] RLS context set correctly
- [ ] Unit tests for business logic
- [ ] Integration tests for API endpoints
- [ ] OpenAPI spec updated

### Frontend
- [ ] No `any` types
- [ ] Accessible (ARIA, keyboard nav)
- [ ] Responsive (mobile/tablet/desktop)
- [ ] Loading/skeleton/error states
- [ ] TanStack Query keys consistent
- [ ] No direct API calls in components
- [ ] Form validation with Zod
- [ ] Component reuse (shadcn/ui)

### Database
- [ ] Migration is reversible
- [ ] Indexes match query patterns
- [ ] RLS policy added
- [ ] Partitioning considered
- [ ] No breaking schema changes (additive only)
- [ ] Seed data for new enums

### DevOps
- [ ] Dockerfile multi-stage
- [ ] Health checks defined
- [ ] Resource limits set
- [ ] Secrets in Key Vault
- [ ] Monitoring alerts updated
- [ ] Runbook updated

---

## Tools & Automation

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
```

### Commitlint
```json
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', ['feat', 'fix', 'chore', 'docs', 'refactor', 'style', 'test', 'perf', 'ci', 'build', 'revert']],
    'scope-enum': [2, 'always', ['auth', 'tally', 'customers', 'invoices', 'payments', 'collections', 'dashboard', 'settings', 'agents', 'sync', 'notifications', 'database', 'infra', 'ui', 'api', 'worker', 'scheduler']]
  }
}
```

### Dependabot
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule: { interval: "weekly" }
  - package-ecosystem: "pip"
    directory: "/apps/backend"
    schedule: { interval: "weekly" }
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
```