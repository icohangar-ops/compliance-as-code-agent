# bd-coach-config

Version-controlled agent behaviour. PR-required changes to prompt, personas, DLP, and topics.

## Layout

```
prompts/     Master system prompt (locked)
personas/    CEO / USA_BD / EU_BD scopes → Keycloak groups
topics/      15 Rasa intents + LibreChat tool mapping
dlp/         HR/compensation regex rules + CI tests
cards/       Adaptive card JSON templates
knowledge/   Connector manifest (Baserow, Nextcloud, Whisper)
```

## CI checks

- `python dlp/run_tests.py` — regex fixtures must pass
- yamllint on all YAML
- CODEOWNERS review on `prompts/`, `personas/`, `dlp/`

## Persona setup

Map Keycloak groups to personas in `personas/personas.yaml`:

| Group | Persona |
|---|---|
| `ceo` | CEO |
| `bd-usa` | USA_BD |
| `bd-eu` | EU_BD |

Default demo users ship in `bd-coach-infra/keycloak/realm-export.json` — change passwords before production.
