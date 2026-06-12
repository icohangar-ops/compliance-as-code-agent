# BD Coach — Fully Open-Source Architecture

**Status:** v2.0 — zero Azure, zero Microsoft 365 dependency  
**License posture:** MIT / Apache-2.0 / AGPL (self-hosted only where noted)

---

## 1. Design goal

Same product behaviour as the original Copilot Studio design — master prompt, 15 topics, persona scopes, points engine, 8 scheduled flows, adaptive cards, DLP audit — on a **100% self-hostable, vendor-neutral** stack. Deploy on any Linux VPS (Hetzner, OVH, DigitalOcean, bare metal, homelab). No Azure subscription, no Entra ID, no Graph API, no SharePoint, no Teams.

---

## 2. Component map

| Layer | Proprietary (old) | OSS replacement | License |
|---|---|---|---|
| Agent UI | Copilot Studio | **LibreChat** | MIT |
| Model gateway | Azure OpenAI | **LiteLLM** → **Ollama** (primary) + optional Groq/OpenRouter | MIT / Apache |
| Topic routing | Copilot topics | **Rasa NLU** | Apache-2.0 |
| Flow engine | Power Automate | **n8n** (self-hosted) | Sustainable Use |
| Chat channel | Teams | **Mattermost Team Edition** | MIT |
| Identity / RBAC | Entra ID | **Keycloak** (OIDC) | Apache-2.0 |
| CRM / pipeline | Monday.com | **Baserow** (REST API, webhooks) | MIT |
| Dashboard / scorecard | Excel on SharePoint | **Baserow** tables (same API) | MIT |
| Documents / KPIs | SharePoint | **Nextcloud** (WebDAV + CalDAV) | AGPL-3.0 |
| Calendar | Outlook | **Nextcloud Calendar** (CalDAV) | AGPL-3.0 |
| Email (optional) | Outlook Graph | **SMTP** (Mailu, Postal, or any relay) | varies |
| Meeting transcripts | Teams API | **Whisper** (faster-whisper) + upload hook | MIT |
| Vector RAG | — | **LlamaIndex ingest** → **Qdrant** | Apache / Apache |
| Object / audit archive | Azure Blob | **MinIO** (S3-compatible, object-lock) | AGPL-3.0 |
| Secrets | Power Automate vault | **HashiCorp Vault** (dev) or n8n credentials | BSL / built-in |
| Logs / observability | Purview | **OpenObserve** + **Prometheus** + **Grafana** | AGPL / Apache |
| TLS / routing | Azure LB | **Traefik** + Let's Encrypt | MIT |
| CI (primary) | — | **GitHub Actions** | — |
| CI (mirror) | — | **Woodpecker CI** on Codeberg | Apache-2.0 |
| Hosting | Azure VMs | **Docker Compose** on any host | — |

**One sentence:** LibreChat + Rasa + LiteLLM + Ollama for the agent; n8n for flows; Mattermost for chat; Keycloak for identity; Baserow + Nextcloud + MinIO for data.

---

## 3. Architecture diagram

```
                         ┌─────────────────────────────────────────┐
                         │           Traefik (TLS + routing)        │
                         └─────────────────────────────────────────┘
    chat.*          bd-coach.*      n8n.*        auth.*       files.*
       │                 │            │            │              │
┌──────▼──────┐   ┌──────▼──────┐ ┌───▼───┐  ┌────▼────┐   ┌─────▼─────┐
│ Mattermost  │   │ LibreChat   │ │  n8n  │  │Keycloak │   │ Nextcloud │
│  BD-Ops     │◄──┤  + Rasa     │ │8 flows│  │  OIDC   │   │ docs/caldav│
└──────┬──────┘   └──────┬──────┘ └───┬───┘  └─────────┘   └─────┬─────┘
       │                 │            │                            │
       │            ┌────▼────┐       │                      ┌─────▼─────┐
       │            │ LiteLLM │       │                      │  Qdrant   │
       │            │ DLP hook│       ├──────────────────────┤  (RAG)    │
       │            └────┬────┘       │                      └───────────┘
       │                 │            │
       │            ┌────▼────┐  ┌────▼────┐  ┌─────────┐  ┌───────────┐
       └────────────┤ Ollama  │  │ Baserow │  │  MinIO  │  │  Whisper  │
                    │ (local) │  │pipeline │  │ audit   │  │transcripts│
                    └─────────┘  │scorecard│  └─────────┘  └───────────┘
                                 └─────────┘
       Postgres · Mongo · Redis · Vault · OpenObserve · Grafana
```

---

## 4. Data plane — 9 knowledge sources (OSS mapping)

| # | Original source | OSS connector | Access pattern |
|---|---|---|---|
| 1 | Monday pipeline | Baserow table `bd_pipeline` | n8n REST + webhooks; per-BD row filter |
| 2 | SharePoint `/BD/2026/` | Nextcloud folder `/BD/2026/` | WebDAV sync → Qdrant every 15 min |
| 3 | Excel dashboard | Baserow tables (weekly, scorecard, commission) | n8n REST; sheet-level ACL in `personas.yaml` |
| 4–5 | KPI docx files | Nextcloud `/BD/Contracts/` | Persona-scoped RAG namespace |
| 6 | Outlook calendar | Nextcloud CalDAV `/remote.php/dav/` | Per-user delegated CalDAV token |
| 7 | Teams transcripts | Whisper API + Nextcloud `/BD/Transcripts/` | Upload or n8n ingest after Jitsi/Mattermost call |
| 8 | Reference library | Nextcloud `/BD/Reference/` | Shared RAG namespace |
| 9 | Activity log | Baserow table `activity_log` | Webhook on row create |

All credentials live in Vault or n8n encrypted store — never in git.

---

## 5. Eight n8n flows (unchanged triggers, OSS actions)

| Flow | Trigger | OSS implementation |
|---|---|---|
| F1 Weekly Push | Mon 09:00 | Baserow → Jinja render → SMTP email + Mattermost DM card |
| F2 Friday Sweep | Fri 18:00 regional | Baserow `weekly_submitted` flag check → reminder → CEO digest queue |
| F3 Hygiene Audit | Daily 02:00 UTC | Baserow `updated_at` stale → Mattermost card |
| F4 Gate Watchdog | Last working day 17:00 | Baserow scorecard fields → Mattermost + escalation row |
| F5 CEO Monday Digest | Mon 08:00 | Aggregate exceptions → SMTP + Mattermost webhook |
| F6 Commission Accrual | Month-end +2 | Baserow formula mirror in Code node → SMTP per BD |
| F7 Deal-Stage Trigger | Baserow webhook | Stage = SSA/Deposit → points update → Mattermost card |
| F8 Monthly 1-pager | Month-end +1 | LibreChat tool → python-docx → Nextcloud WebDAV upload |

Each flow: 3× retry, Postgres dead-letter table, Mattermost alert on failure.

---

## 6. Security model

- **Identity:** Keycloak realm `bd-coach`; groups `ceo`, `bd-usa`, `bd-eu` map to personas via `personas.yaml`.
- **Channel ACL:** Mattermost private channel `bd-ops`; per-persona DM channels enforced by Mattermost.
- **DLP:** LiteLLM post-call hook loads `dlp/restricted_hr_comp.yaml`; blocks HR/comp leakage to non-CEO personas.
- **Audit:** Every prompt/response → Postgres `audit.events`; daily mirror to MinIO with object-lock (24-month retention).
- **Config governance:** Prompt, personas, DLP in `bd-coach-config` repo; PR + CODEOWNERS required.

---

## 7. Deployment topology

### Single-node (dev / small team)

```bash
cd bd-coach-infra
cp .env.example .env   # fill DOMAIN, passwords, optional Groq key
docker compose -f compose/docker-compose.yml up -d
./scripts/bootstrap.sh
```

### Production (recommended)

| Role | Spec | Notes |
|---|---|---|
| Primary host | 8 vCPU / 32 GB RAM / 500 GB NVMe | Runs full compose; Ollama needs RAM for 8B+ models |
| Standby host | Same spec, different region | Postgres logical replication + MinIO bucket mirror |
| DNS | A records: `chat`, `bd-coach`, `n8n`, `auth`, `files`, `data`, `api` → primary IP | Let's Encrypt via Traefik |
| Backups | MinIO → second site or Backblaze B2 | Nightly Postgres + Qdrant snapshots |

**Model sizing:** CEO persona → `llama3.1:70b` or cloud failover; BD personas → `llama3.1:8b` or `mistral:7b`. Adjust in `litellm/config.yaml`.

---

## 8. Repository layout (3 repos)

```
bd-coach-config/   # Prompt, personas, topics, DLP, cards, knowledge manifest
n8n-flows/         # 8 flow JSON exports
bd-coach-infra/    # Compose, LiteLLM, LibreChat, Keycloak realm, CI/CD
```

Mirror all three to Codeberg; GitHub Actions pushes to Codeberg on `main`.

---

## 9. Accounts you need (no Azure)

See `ACCOUNTS_CHECKLIST.md`. Summary:

| Priority | Service | Cost |
|---|---|---|
| P0 | VPS host (Hetzner CPX41 or equiv.) | ~€40–80/mo |
| P0 | Domain + DNS | ~€12/yr |
| P0 | Mattermost (self-hosted in compose) | $0 |
| P0 | Keycloak (self-hosted in compose) | $0 |
| P1 | GitHub org + 3 repos | $0 |
| P1 | Codeberg org + mirror | $0 |
| P1 | Optional Groq/OpenRouter API (failover / CEO tier) | ~$0–100/mo |
| P2 | Backblaze B2 off-site backup | ~$5/mo |

**Estimated all-in:** ~$60–150/mo depending on VPS and optional cloud LLM failover.

---

## 10. Migration from v1 (Azure-hybrid) scaffold

| Remove | Replace with |
|---|---|
| `ENTRA_*` env vars | `KEYCLOAK_*` |
| `AZURE_OPENAI_*` | `OLLAMA_BASE_URL` + optional `GROQ_API_KEY` |
| `GRAPH_*`, `WORKBOOK_ID` | `BASEROW_*`, `NEXTCLOUD_*` |
| `MONDAY_*` | `BASEROW_TABLE_PIPELINE`, `BASEROW_TABLE_ACTIVITY` |
| `TEAMS_WEBHOOK_*` | `MM_HOOK_CEO_DIGEST` |
| Azure deploy workflow | SSH deploy to `$DEPLOY_HOST` |

Behaviour, prompts, topics, points engine, and adaptive cards are unchanged.
