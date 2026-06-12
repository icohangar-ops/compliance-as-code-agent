#!/usr/bin/env bash
# Initialize git repos for the three BD Coach packages and add GitHub + Codeberg remotes.
# Does NOT push — review remotes, then: git push -u github main && git push -u codeberg main
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

GITHUB_OWNER="${GITHUB_OWNER:-}"
CODEBERG_OWNER="${CODEBERG_OWNER:-}"
USE_SSH="${USE_SSH:-Y}"

[[ -z "${GITHUB_OWNER}" ]] && read -rp "GitHub owner (user or org): " GITHUB_OWNER
[[ -z "${CODEBERG_OWNER}" ]] && read -rp "Codeberg owner (user or org): " CODEBERG_OWNER
if [[ -z "${USE_SSH_SET:-}" ]]; then
  read -rp "Use SSH remotes? [Y/n]: " USE_SSH
  USE_SSH="${USE_SSH:-Y}"
fi

if [[ "${USE_SSH}" =~ ^[Yy] ]]; then
  github_url() { echo "git@github.com:${GITHUB_OWNER}/$1.git"; }
  codeberg_url() { echo "git@codeberg.org:${CODEBERG_OWNER}/$1.git"; }
else
  echo "HTTPS mode: you will be prompted for PAT on first push (or use gh auth login)."
  github_url() { echo "https://github.com/${GITHUB_OWNER}/$1.git"; }
  codeberg_url() { echo "https://codeberg.org/${CODEBERG_OWNER}/$1.git"; }
fi

REPOS=(bd-coach-config n8n-flows bd-coach-infra)

for repo in "${REPOS[@]}"; do
  dir="${ROOT}/${repo}"
  [[ -d "${dir}" ]] || { echo "Missing ${dir}"; exit 1; }

  echo ""
  echo "=== ${repo} ==="
  cd "${dir}"

  if [[ ! -d .git ]]; then
    git init
    git branch -M main
  fi

  git remote remove github 2>/dev/null || true
  git remote remove codeberg 2>/dev/null || true
  git remote add github "$(github_url "${repo}")"
  git remote add codeberg "$(codeberg_url "${repo}")"

  # Per-repo gitignore
  if [[ ! -f .gitignore ]]; then
  cat > .gitignore <<'EOF'
.env
*.env.local
.venv/
EOF
  fi

  git add -A
  if git diff --cached --quiet; then
    echo "Nothing to commit in ${repo}"
  else
    git commit -m "Initial BD Coach ${repo} scaffold (OSS v2)"
  fi

  echo "Remotes:"
  git remote -v
  echo "Push when ready:"
  echo "  cd ${dir} && git push -u github main && git push -u codeberg main"
done

echo ""
echo "Done. Create empty repos on GitHub and Codeberg first if you have not already."
