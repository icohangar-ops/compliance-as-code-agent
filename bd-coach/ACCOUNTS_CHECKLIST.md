# BD Coach — Accounts & Services Checklist

**Target:** All P0 items before first deploy  
**Principle:** Self-hosted OSS first; optional SaaS only for LLM failover

---

## P0 — Required before go-live

| # | Service | Who | What you need | Why |
|---|---|---|---|---|
| 1 | **VPS / bare metal** (Hetzner CPX41, OVH, DO, etc.) | Ops | 8 vCPU, 32 GB RAM, 500 GB disk; Ubuntu 24.04; SSH key | Hosts entire Docker stack |
| 2 | **Domain + DNS** | Ops | `A` records: `chat`, `bd-coach`, `n8n`, `auth`, `files`, `data`, `api`, `minio` → host IP | TLS via Let's Encrypt |
| 3 | **Mattermost** | Self-hosted in compose | Create channel `bd-ops` (private), bot `bd-coach-bot`, incoming webhooks F1/F3/F4/F7 | Primary chat surface |
| 4 | **Keycloak** | Self-hosted in compose | Realm `bd-coach`; users for CEO + 2 BDs; groups map to personas | OIDC for all UIs |
| 5 | **Baserow** | Self-hosted in compose | Tables: `bd_pipeline`, `activity_log`, `weekly_reports`, `scorecard`, `commission` | Replaces Monday + Excel |
| 6 | **Nextcloud** | Self-hosted in compose | Folders: `/BD/2026/`, `/BD/Contracts/`, `/BD/Reference/`, `/BD/Transcripts/` | Documents + CalDAV |

---

## P1 — Needed for test week

| # | Service | Notes |
|---|---|---|
| 7 | **GitHub** org + 3 repos: `bd-coach-config`, `n8n-flows`, `bd-coach-infra` | Branch protection on `main`; PAT with `repo` + `workflow` for CI |
| 8 | **Codeberg** org + same 3 repo names | Mirror from GitHub; Woodpecker CI for lint + DLP tests |
| 9 | **SMTP relay** (optional) | Mailu in compose, or SendGrid/Postmark/any SMTP for F1/F5/F6 emails |
| 10 | **Groq or OpenRouter API key** (optional) | CEO-tier failover when local Ollama is slow; set monthly cap |
| 11 | **Mattermost CEO digest webhook** | One incoming webhook URL → `MM_HOOK_CEO_DIGEST` in `.env` |

---

## P2 — Within first 30 days

| # | Service | Notes |
|---|---|---|
| 12 | **MinIO off-site mirror** or Backblaze B2 | Nightly audit archive + DB snapshots (~$5/mo) |
| 13 | **Standby host** (second region) | Postgres replication + MinIO sync; documented in infra README |
| 14 | **Better Stack / Uptime Kuma** | On-call alerting during hyper-care week |

---

## Environment variables checklist

Copy `bd-coach-infra/.env.example` → `.env` and fill:

```
BD_COACH_DOMAIN=example.com
PG_PASSWORD=...
KEYCLOAK_ADMIN_PASSWORD=...
BASEROW_TOKEN=...
NEXTCLOUD_APP_PASSWORD=...
MM_HOOK_F1 / F3 / F4 / F7 / CEO_DIGEST=...
SMTP_HOST / SMTP_USER / SMTP_PASS=...
GROQ_API_KEY=...          # optional
MINIO_ROOT_PASSWORD=...
```

---

## Estimated monthly cost

| Line | USD/mo |
|---|---|
| VPS (primary) | 45–80 |
| Domain | 1 |
| Groq/OpenRouter (optional failover) | 0–100 |
| Off-site backup | 5 |
| All OSS (LibreChat, n8n, Mattermost, Keycloak, Ollama, etc.) | 0 |
| **Total** | **~60–150** |

---

## What to confirm before build kick-off

1. Approve OSS architecture (`ARCHITECTURE.md`)
2. Mattermost workspace ready — admin invite + `bd-ops` channel
3. VPS provisioned + DNS records set
4. GitHub + Codeberg orgs created with empty repos
5. 30-min slot for DLP rules review (`bd-coach-config/dlp/`)
