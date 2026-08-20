# ADR-007: Frontend Stack - Next.js 14 + shadcn/ui + TanStack Query

## Context
CredFlow frontend requirements:
- Dashboard with real-time KPIs, aging charts, top debtors
- Customer/invoice management with complex filtering/sorting
- Reminder template builder, campaign management
- Payment link creation, public payment portal
- Settings: team, Tally sync, templates, schedules, billing
- Multi-tenant (tenant context from auth)
- Responsive (desktop primary, tablet/mobile for dashboards)
- Type-safe API integration
- Fast development iteration

## Decision
Use **Next.js 14 (App Router)** with **React 18**, **TypeScript**, **TanStack Query v5**, **shadcn/ui** (Radix UI + Tailwind CSS).

### Stack Summary
| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | Next.js 14 (App Router) | SSR for auth/pages, RSC for performance, built-in routing |
| Language | TypeScript (strict) | End-to-end type safety with OpenAPI-generated types |
| State/Server | TanStack Query v5 | Server state caching, mutations, optimistic updates |
| UI Components | shadcn/ui (Radix + Tailwind) | Accessible, customizable, copy-paste ownership |
| Styling | Tailwind CSS | Utility-first, consistent design system |
| Forms | React Hook Form + Zod | Type-safe validation, schema sharing with backend |
| Charts | Recharts / Tremor | React-native, responsive, accessible |
| Auth | Keycloak JS Adapter / NextAuth v5 | OIDC integration with Keycloak (local) → Azure Entra ID (prod) |
| HTTP Client | Fetch + TanStack Query | Native, no extra deps, works with SWR patterns |

### Project Structure
```
apps/web/
├── src/
│   ├── app/                    # App Router pages
│   │   ├── (auth)/             # Login, callback, invite
│   │   ├── (dashboard)/        # Protected dashboard routes
│   │   │   ├── dashboard/      # KPIs, aging, cashflow
│   │   │   ├── customers/      # List, detail, timeline
│   │   │   ├── invoices/       # List, detail, aging
│   │   │   ├── collections/    # Tasks, campaigns
│   │   │   ├── payments/       # Links, history
│   │   │   ├── reports/        # Aging, outstanding, collection
│   │   │   └── settings/       # Team, tally, templates, schedule, billing
│   │   ├── pay/[token]/        # Public payment portal
│   │   ├── layout.tsx          # Root layout, providers
│   │   └── globals.css         # Tailwind + CSS variables
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── charts/             # Chart wrappers (Recharts)
│   │   ├── forms/              # Form components (RHF + Zod)
│   │   └── layout/             # Sidebar, header, breadcrumbs
│   ├── lib/
│   │   ├── api.ts              # TanStack Query hooks (generated)
│   │   ├── auth.ts             # Auth helpers, token management
│   │   ├── utils.ts            # Formatters, helpers
│   │   └── validations/        # Zod schemas (shared with backend)
│   ├── hooks/                  # Custom React hooks
│   └── types/                  # Generated from OpenAPI
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

### Auth Flow
1. User visits `/` → redirected to `/login`
2. `/login` → "Login with Azure/Keycloak" → redirects to Keycloak
3. Keycloak redirects to `/auth/callback?code=...`
4. `/auth/callback` exchanges code for tokens, sets HttpOnly cookies
4. Redirect to `/dashboard` with tenant context

### API Integration
- OpenAPI spec → `openapi-typescript-codegen` → typed TanStack Query hooks
- All API calls go through `/api/v1/` prefix
- Automatic token refresh via axios/fetch interceptor
- Optimistic updates for mutations (reminder send, payment link create)

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Vite + React SPA** | Simple, fast HMR | No SSR (SEO, auth), manual routing, no RSC |
| **Remix** | Great data loading, nested routes | Smaller ecosystem, team less familiar |
| **Next.js Pages Router** | Mature | Legacy, no RSC, App Router is future |
| **Next.js 14 App Router** | RSC, SSR, nested layouts, streaming, Server Actions | Learning curve, but team can adapt |

## Consequences

**Positive:**
- **Server Components** reduce client bundle, improve performance
- **Built-in SSR** for auth pages, SEO, initial data loading
- **TanStack Query** eliminates manual fetch state, provides caching/invalidation
- **shadcn/ui** = accessible components we own (no version lock-in)
- **Tailwind** = consistent design system, dark mode ready
- **TypeScript end-to-end** via OpenAPI codegen
- **Vercel/Azure Static Web Apps** deployment parity
- **App Router layouts** = perfect for dashboard sidebar + nested routes

**Negative:**
- **App Router learning curve** (Server vs Client Components, Suspense boundaries)
- **Hydration mismatch risks** with server/client boundary
- **Larger bundle** than Vite SPA (mitigated: RSC reduces client JS)
- **Team needs Next.js 14 experience** (training budget week 1)

## Implementation Notes
- `next.config.js`: `output: 'standalone'` for Docker, `transpilePackages: ['@credflow/*']`
- Path aliases from `tsconfig.base.json` work via `next-transpile-modules` or Turborepo
- Tailwind: CSS variables for theming (light/dark), `credflow` color palette
- Charts: Recharts for flexibility, Tremor for pre-built dashboard components
- Public payment page (`/pay/[token]`) = static export possible (no auth)
- Error boundaries per route segment for graceful degradation
- Middleware for auth protection (redirects to login if no valid session)