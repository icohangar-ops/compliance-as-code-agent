# Publishing Tech Economist

Standalone repo published to three remotes:

| Remote | URL |
|--------|-----|
| Codeberg | `https://codeberg.org/cubiczan/tech-economist` |
| GitHub (org) | `https://github.com/icohangar-ops/tech-economist` |
| GitHub (user) | `https://github.com/cubiczan/tech-economist` |

## One-time setup

### 1. Create empty repos (if they do not exist)

On each host, create a **private or public** empty repo named `tech-economist` (no README, no .gitignore).

- Codeberg: https://codeberg.org/repo/create
- GitHub icohangar-ops: https://github.com/organizations/icohangar-ops/repositories/new
- GitHub cubiczan: https://github.com/new

### 2. Initialize and wire remotes

```bash
cd tech-economist
chmod +x scripts/*.sh start.sh
./scripts/publish-init-repo.sh
```

Optional auto-create (if tokens are configured):

```bash
export CODEBERG_TOKEN="..."   # Codeberg → Settings → Applications → Generate Token
export CREATE_REPOS=1
gh auth login                 # for GitHub repo create
./scripts/publish-init-repo.sh
```

### 3. Push

```bash
./scripts/publish-push.sh
```

Or individually:

```bash
git push -u codeberg main
git push -u github-icohangar main
git push -u github-cubiczan main
```

## SSH remotes

```bash
USE_SSH=Y ./scripts/publish-init-repo.sh
```

## Notes

- This directory must be its **own git root**, not nested inside `compliance-as-code-agent` when publishing.
- `backend/data/*.db`, `.venv/`, `node_modules/`, and `dist/` are gitignored.
