# n8n-flows

Eight scheduled and webhook flows — OSS connectors only (Baserow, SMTP, Mattermost, Nextcloud).

| Flow | Trigger | Actions |
|---|---|---|
| F1 | Mon 09:00 | Baserow pipeline → SMTP + Mattermost DM |
| F2 | Fri 18:00 | Baserow weekly flag → SMTP reminder |
| F3 | Daily 02:00 UTC | Stale deals → Mattermost card |
| F4 | Month-end 17:00 | Scorecard <25 pts → Mattermost alert |
| F5 | Mon 08:00 | Exception digest → SMTP + Mattermost CEO webhook |
| F6 | Month +2 days | Commission calc → SMTP per BD |
| F7 | Baserow webhook | Stage SSA/Deposit → points + Mattermost |
| F8 | Month +1 day | LibreChat 1-pager → Nextcloud WebDAV |

## Import

1. Open n8n at `https://n8n.${BD_COACH_DOMAIN}`
2. Settings → Import from file → select each JSON in `flows/`
3. Set credentials: SMTP, Postgres (audit), HTTP header auth for Baserow
4. Activate flows after Baserow table IDs are in `.env`

## Baserow webhooks

Configure F7 webhook URL: `https://n8n.${BD_COACH_DOMAIN}/webhook/baserow-deal-stage`
