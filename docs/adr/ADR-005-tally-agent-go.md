# ADR-005: Tally Agent Architecture - Go Binary

## Context
CredFlow needs a local Windows agent that:
- Runs on customer's Windows machine (where Tally ERP is installed)
- Connects to Tally's local HTTP XML API (typically `http://localhost:9000`)
- Extracts data: Companies, Ledgers (customers), Sales Vouchers (invoices), Receipt Vouchers (payments)
- Queues data locally when internet is down
- Securely uploads to cloud API
- Auto-updates silently
- Runs as Windows Service (auto-start, recovery)
- Zero customer IT involvement for installation

## Decision
Build the Tally Agent in **Go (Golang)** as a single static binary.

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Tally Agent (Go)                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Tally XML   │  │ Local SQLite│  │ Upload Engine       │  │
│  │ Poller      │──►│ Queue       │──►│ (HTTPS + Retry)     │  │
│  │ (Scheduler) │  │ (WAL mode)  │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Config Mgr  │  │ Health      │  │ Auto-Updater        │  │
│  │ (YAML/Reg)  │  │ Reporter    │  │ (GitHub Releases)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components
1. **Tally XML Poller**: Configurable interval (default 15 min), builds ENVELOPE requests, parses responses
2. **Local SQLite Queue**: WAL mode for durability, stores pending sync payloads, tracks last sync timestamp per entity
3. **Upload Engine**: HTTPS POST to `/api/v1/tally/sync`, exponential backoff retry, compression (gzip)
4. **Health Reporter**: Heartbeat to `/api/v1/agents/heartbeat` every 5 min
5. **Config Manager**: Reads `config.yaml` (Tally URL, API endpoint, auth token, sync schedule)
6. **Auto-Updater**: Checks GitHub Releases on startup, downloads new binary, replaces self, restarts

### Windows Service Wrapper
- Uses `golang.org/x/sys/windows/svc`
- Auto-start on boot, recovery on crash (restart after 30s, max 3 retries)
- Event log integration for debugging

### Installer
- Inno Setup / NSIS installer
- Prompts for: Registration token, Tally HTTP port, Sync interval
- Registers Windows Service, starts it
- Creates desktop shortcut for manual sync trigger

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Python (PyInstaller)** | Easy XML parsing, team knows Python | Large binary (~50MB), runtime dependencies, slower startup, antivirus false positives |
| **C# / .NET** | Native Windows, great service support | Requires .NET runtime, larger install, team less experienced |
| **Go** | Single static binary (~8MB), no runtime, fast, cross-compile from Linux/Mac, excellent Windows service support | Team needs Go basics (but simple enough) |
| **Electron/Node.js** | Web tech stack | Heavy (~100MB), not suitable for background service |

## Consequences

**Positive:**
- **Single 8MB binary** - no install, no runtime, easy distribution
- **Cross-compile from CI** - build Windows `.exe` from Linux/GitHub Actions
- **Native Windows Service** - robust, auto-recovery, event logs
- **SQLite embedded** - no separate DB install, WAL mode survives power loss
- **Fast startup** - critical for scheduled tasks
- **Memory efficient** - runs in <20MB RAM
- **Strong XML parsing** - `encoding/xml` + custom structs

**Negative:**
- Team needs basic Go knowledge (mitigated: agent is ~500 lines, simple logic)
- Separate codebase from Python backend (but clear API contract)

## Implementation Notes
- Build: `GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o tally-agent.exe`
- CI: GitHub Actions builds on every tag, uploads to GitHub Releases
- Config: `config.yaml` in same directory as binary (or `%PROGRAMDATA%\CredFlow\`)
- Auth: Agent API key (SHA256 stored in cloud, sent via `X-Agent-Key` header)
- Sync payload: JSON with `companies[]`, `customers[]`, `invoices[]`, `payments[]`, `synced_at`
- Delta sync: Track `last_sync_timestamp` per entity type in SQLite
- Retry: Exponential backoff (1m, 2m, 4m, 8m, max 1h) with jitter
- Logging: Structured JSON to file + Windows Event Log