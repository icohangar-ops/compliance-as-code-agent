# Publishing BD Coach to GitHub + Codeberg

Three repositories (as designed). You can push now and deploy later when you have the green light.

| Repo | Contents |
|---|---|
| `bd-coach-config` | Prompt, personas, topics, DLP, cards |
| `n8n-flows` | Eight n8n flow JSON files |
| `bd-coach-infra` | Docker Compose, Keycloak, LiteLLM, CI/CD |

---

## Before you push

- `.env` is **gitignored** — never commit it (contains Groq key + passwords).
- Only `.env.example` goes in git (no real secrets).
- Rotate your Groq key if it was ever pasted in chat.

```bash
# Verify no secrets staged
git status
git check-ignore -v bd-coach-infra/.env   # must show as ignored
```

---

## Step 1 — Create empty repos

### GitHub

Create **3 private repos** (no README, no .gitignore — empty):

- `bd-coach-config`
- `n8n-flows`
- `bd-coach-infra`

Org or personal account — note the owner name (e.g. `myorg`).

### Codeberg

Same three names under your Codeberg org/user:

- `codeberg.org/myorg/bd-coach-config`
- `codeberg.org/myorg/n8n-flows`
- `codeberg.org/myorg/bd-coach-infra`

---

## Step 2 — Create PATs

### GitHub PAT (for pushing from your laptop)

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens**
2. **Fine-grained** (recommended) or **Classic**
3. Scopes needed:
   - `Contents`: Read and write
   - `Workflow`: Read and write (if you want CI to run on push)
4. Copy the token once — you won’t see it again.

**Where to use it (pick one):**

| Method | Where to enter PAT |
|---|---|
| **GitHub CLI** (easiest) | Terminal: `gh auth login` → paste PAT when prompted |
| **Git credential helper** | macOS Keychain stores it after first `git push` |
| **Remote URL** (not recommended) | `https://<PAT>@github.com/OWNER/bd-coach-config.git` — leaks in shell history |

```bash
gh auth login
# GitHub.com → HTTPS → Paste token → Login with a web browser OR paste token
```

### Codeberg PAT (for mirror + Woodpecker)

1. Codeberg → avatar → **Settings** → **Applications**
2. **Generate New Token**
3. Scopes: `read:user`, `read:repository`, `write:repository`
4. Copy the token.

**Where to use it:**

| Use | Where |
|---|---|
| **Push from laptop** | `git remote add codeberg https://<TOKEN>@codeberg.org/OWNER/bd-coach-config.git` or store in credential helper |
| **GitHub Actions mirror** | GitHub → each repo → **Settings** → **Secrets and variables** → **Actions** → `CODEBERG_TOKEN` |
| **Woodpecker CI** | Codeberg repo → **Settings** → **Secrets** (if workflows need API access) |

---

## Step 3 — Push the three repos from this folder

From your Mac, the scaffold lives inside the compliance-as-code-agent project:

```bash
cd ~/Projects/compliance-as-code-agent/bd-coach
chmod +x scripts/publish-init-repos.sh
./scripts/publish-init-repos.sh
```

(Not `~/bd-coach` — unless you copy or symlink it there yourself.)

The script will prompt for `GITHUB_OWNER` and `CODEBERG_OWNER`, then init git in each subfolder and add remotes. You push with `gh` or git after reviewing.

**Manual alternative** (one repo example):

```bash
cd bd-coach/bd-coach-config
git init
git add .
git commit -m "Initial BD Coach config scaffold (OSS v2)"
git branch -M main
git remote add github git@github.com:OWNER/bd-coach-config.git
git remote add codeberg git@codeberg.org:OWNER/bd-coach-config.git
git push -u github main
git push -u codeberg main
```

Repeat for `n8n-flows` and `bd-coach-infra`.

SSH remotes avoid embedding PATs in URLs if you use SSH keys on GitHub/Codeberg.

---

## Step 4 — GitHub Actions secrets (per repo)

Set these in **GitHub → repo → Settings → Secrets and variables → Actions**.

### All three repos

Usually none required for basic CI (lint + DLP tests use only the checkout).

### `bd-coach-infra` only

| Secret | Required now? | Purpose |
|---|---|---|
| `CODEBERG_TOKEN` | Optional | Auto-mirror `main` to Codeberg on push |
| `DEPLOY_HOST` | Later | Hostinger VPS IP — when you deploy |
| `DEPLOY_USER` | Later | e.g. `bdcoach` |
| `DEPLOY_SSH_KEY` | Later | Private SSH key for VPS deploy job |

### `bd-coach-infra` — Repository variables

**Settings → Secrets and variables → Actions → Variables**

| Variable | Example | Purpose |
|---|---|---|
| `CODEBERG_ORG` | `myorg` | Mirror target org/user on Codeberg |

---

## Step 5 — Codeberg Woodpecker

For each Codeberg repo:

1. **Settings** → **Actions** → enable **Woodpecker CI**
2. Woodpecker reads `.woodpecker/ci.yaml` from the repo root
3. `bd-coach-config` and `bd-coach-infra` include Woodpecker configs; `n8n-flows` runs JSON lint in GitHub Actions only

No PAT needed in Woodpecker for basic lint unless you add deploy steps later.

---

## Step 6 — Branch protection (recommended)

On **GitHub** for each repo:

- **Settings → Branches → Add rule** on `main`
- Require PR before merge
- Require status checks: `validate` (and `dlp-rules-test` on config repo)
- Add `CODEOWNERS` reviewers for `bd-coach-config`

Mirror the same policy on Codeberg if your team merges there.

---

## What runs on push

| Repo | GitHub Actions | Codeberg Woodpecker |
|---|---|---|
| `bd-coach-config` | yamllint + DLP tests | Same |
| `n8n-flows` | JSON lint | — |
| `bd-coach-infra` | compose validate, Trivy, optional Codeberg mirror | yamllint + compose + DLP |

Deploy to Hostinger is **skipped** until you set `DEPLOY_*` secrets and run workflow manually (or on push to `main`).

---

## After green light (deploy)

1. Copy `.env.example` → `.env` on VPS (never commit)
2. Set GitHub secrets `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`
3. Run **Actions → deploy → Run workflow** on `bd-coach-infra`

Or SSH deploy manually per `bd-coach-infra/docs/HOSTINGER.md`.

---

## Quick reference — where PATs go

```
┌─────────────────────────────────────────────────────────────┐
│ YOUR LAPTOP                                                  │
│  gh auth login                    → GitHub PAT (push/pull)    │
│  git push codeberg                → Codeberg PAT (once)       │
│  ~/.ssh/id_ed25519                → alternative to PATs       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ GITHUB → bd-coach-infra → Settings → Secrets → Actions      │
│  CODEBERG_TOKEN                   → Codeberg mirror PAT     │
│  DEPLOY_HOST / DEPLOY_USER /      → later (Hostinger)       │
│  DEPLOY_SSH_KEY                                              │
│ Variables: CODEBERG_ORG           → Codeberg username/org     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ VPS / RUNTIME                                                │
│  bd-coach-infra/.env              → Groq, SMTP, MM hooks     │
│  (scp manually — never in git)                              │
└─────────────────────────────────────────────────────────────┘
```
