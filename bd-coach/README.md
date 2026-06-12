# BD Coach — Open-Source Sales Operations Agent

A self-hosted conversational layer and flow engine for business-development teams. Replaces Copilot Studio + Power Automate with LibreChat, n8n, Mattermost, and a fully open-source data plane.

## Repositories

```
bd-coach/
├── bd-coach-config/   # Prompt, personas, topics, DLP, cards, knowledge sources
├── n8n-flows/         # 8 scheduled/webhook flows
├── bd-coach-infra/    # Docker Compose, LiteLLM, Keycloak, CI/CD
├── ARCHITECTURE.md    # Full OSS design (read this first)
└── ACCOUNTS_CHECKLIST.md
```

## Stack

```
┌────────────┐    ┌──────────┐   ┌─────────────────────────┐
│ Mattermost │◄───┤ LibreChat├──►│ LiteLLM ──► Ollama (local)│
│  (chat)    │    │ (agent)  │   │          ► Groq (optional)│
└─────┬──────┘    └────┬─────┘   └─────────────────────────┘
      │                │
      │            ┌───┴────┐
      │            │  Rasa  │  topic classifier (T01–T15)
      │            └────────┘
      │
      │     ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐
      └─────┤   n8n    ├──┤ Baserow  │  │Nextcloud │  │ MinIO  │
            │ 8 flows  │  │ pipeline │  │ docs/cal │  │ audit  │
            └──────────┘  └──────────┘  └──────────┘  └────────┘
   Traefik + TLS · Keycloak OIDC · Vault · OpenObserve · Qdrant
```

## Quick start

```bash
cd bd-coach-infra
cp .env.example .env
# Set BD_COACH_DOMAIN, passwords, and optional GROQ_API_KEY
docker compose -f compose/docker-compose.yml up -d
./scripts/bootstrap.sh
```

Open `https://bd-coach.${BD_COACH_DOMAIN}` after DNS propagates.

## What's locked (config repo)

| Path | Purpose |
|---|---|
| `prompts/bd_coach.v1.0.md` | Master system prompt |
| `personas/personas.yaml` | CEO / BD_USA / BD_EU scopes |
| `topics/topics.yaml` | 15 conversational topics |
| `dlp/restricted_hr_comp.yaml` | HR/compensation DLP rules |
| `cards/*.json` | Adaptive card templates |
| `knowledge/sources.yaml` | 9 data source connectors |

## Publishing

Push the three subdirectories as **separate repos** to GitHub and Codeberg.

**Full guide (PAT locations, secrets, step-by-step):** [`PUBLISHING.md`](PUBLISHING.md)

```bash
cd bd-coach
./scripts/publish-init-repos.sh   # init git + remotes in each repo
# then per repo: git push -u github main && git push -u codeberg main
```

## Cost

~$60–150/mo (VPS + optional cloud LLM failover). See `ARCHITECTURE.md` §9 and `ACCOUNTS_CHECKLIST.md`.
