# Compliance-as-Code Agent

Rust agent that scans codebases against organizational compliance policies and auto-fixes violations.

Built by [Cubiczan](https://codeberg.org/cubiczan) — composes patterns from [Consensus Hardening Protocol](https://codeberg.org/cubiczan/consensus-hardening-protocol) and [ABOS governance-core](https://codeberg.org/cubiczan/autonomous-business-os).

## What it does

| Agent | Role |
|-------|------|
| **Detector** | Walks the repo and evaluates YAML policy packs |
| **Fixer** | Proposes and applies rule-based auto-fixes |
| **Validator** | Re-scans + CHP-style adversarial review |

Every check and fix is logged to a signed append-only audit ledger (`.cac/audit.jsonl`).

## Policy packs (included)

- **no-hardcoded-secrets** — API keys, passwords, tokens, `.env` commits (SOC2)
- **gdpr-data-tagging** — `@gdpr` annotations on PII fields
- **soc2-audit-trails** — `audit_log` calls on auth, delete, and payment handlers

## Quick start

```bash
cargo build --release
cargo run -p cac-cli -- scan --root examples/violations
cargo run -p cac-cli -- run --root examples/violations --dry-run
```

## CLI

```bash
cac scan              # Detector agent
cac fix [--dry-run]   # Fixer agent
cac validate          # Validator agent
cac run [--dry-run]   # Full detect → fix → validate pipeline
cac audit             # Show signed audit trail
cac serve             # PR webhook server (GitHub + Codeberg)
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `.` | Repository root to scan |
| `--policies` | `policies` | Policy YAML directory |
| `--format` | `text` | `text` or `json` |
| `--signing-key` | env `CAC_LEDGER_SIGNING_KEY` | HMAC key for audit signatures |

## Architecture

```
policies/*.yaml
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌────────────────┐
│ cac-scanner │───▶│  cac-fixer  │───▶│ cac-validator  │
│  (detect)   │    │   (fix)     │    │  (validate)    │
└──────┬──────┘    └──────┬──────┘    └───────┬────────┘
       │                  │                    │
       └──────────────────┴────────────────────┘
                          │
                    cac-core (policy + audit ledger)
                          │
                    .cac/audit.jsonl
```

## PR webhook integration

Run the webhook server to scan pull requests automatically:

```bash
cp .env.example .env   # set CAC_WEBHOOK_SECRET, tokens
cac serve --policies policies
```

On each `pull_request` event (opened, synchronized, reopened):

1. **Detector** clones the PR head and scans against policies
2. Posts **commit status** (`compliance-as-code/scan`) — pass or fail
3. Posts a **PR comment** with violation details
4. Optionally opens an **auto-fix PR** when `CAC_AUTO_FIX_PR=true`

See [docs/WEBHOOK_SETUP.md](docs/WEBHOOK_SETUP.md) for GitHub and Codeberg webhook configuration.

## CI integration

```yaml
- run: cargo build --release -p cac-cli
- run: ./target/release/cac scan --format json
  env:
    CAC_LEDGER_SIGNING_KEY: ${{ secrets.CAC_LEDGER_SIGNING_KEY }}
```

Exit code `1` when critical violations remain after validation.

## Air-gap / regulated deployments

- Static policy engine runs fully offline — no LLM required for detection
- Single binary (`cac`) suitable for on-prem CI and air-gapped environments
- Signed audit ledger provides SOC2 evidence chain

## License

MIT — see [LICENSE](LICENSE).
