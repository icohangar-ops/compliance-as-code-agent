#!/usr/bin/env bash
# Initialize tech-economist as a standalone repo and wire remotes for Codeberg + GitHub.
# Create empty repos first, or set CODEBERG_TOKEN / run `gh auth login` for auto-create.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_NAME="tech-economist"
CODEBERG_OWNER="${CODEBERG_OWNER:-cubiczan}"
GITHUB_ICOHANGAR_OWNER="${GITHUB_ICOHANGAR_OWNER:-icohangar-ops}"
GITHUB_CUBICZAN_OWNER="${GITHUB_CUBICZAN_OWNER:-cubiczan}"
USE_SSH="${USE_SSH:-N}"

cd "${ROOT}"

if git rev-parse --show-toplevel 2>/dev/null | grep -qv "${ROOT}$"; then
  echo "ERROR: tech-economist is inside another git repo ($(git rev-parse --show-toplevel))."
  exit 1
fi

if [[ "${USE_SSH}" =~ ^[Yy] ]]; then
  codeberg_url() { echo "git@codeberg.org:${CODEBERG_OWNER}/${REPO_NAME}.git"; }
  github_icohangar_url() { echo "git@github.com:${GITHUB_ICOHANGAR_OWNER}/${REPO_NAME}.git"; }
  github_cubiczan_url() { echo "git@github.com:${GITHUB_CUBICZAN_OWNER}/${REPO_NAME}.git"; }
else
  codeberg_url() { echo "https://codeberg.org/${CODEBERG_OWNER}/${REPO_NAME}.git"; }
  github_icohangar_url() { echo "https://github.com/${GITHUB_ICOHANGAR_OWNER}/${REPO_NAME}.git"; }
  github_cubiczan_url() { echo "https://github.com/${GITHUB_CUBICZAN_OWNER}/${REPO_NAME}.git"; }
fi

if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git remote remove codeberg 2>/dev/null || true
git remote remove github-icohangar 2>/dev/null || true
git remote remove github-cubiczan 2>/dev/null || true
git remote add codeberg "$(codeberg_url)"
git remote add github-icohangar "$(github_icohangar_url)"
git remote add github-cubiczan "$(github_cubiczan_url)"

git add -A
if git diff --cached --quiet; then
  echo "Nothing to commit."
else
  git commit -m "Initial Tech Economist CFO dashboard for AI token ROI tracking."
fi

create_codeberg_repo() {
  if [[ -z "${CODEBERG_TOKEN:-}" ]]; then
    echo "Skip Codeberg create: set CODEBERG_TOKEN to auto-create."
    return 1
  fi
  curl -fsS -X POST "https://codeberg.org/api/v1/user/repos" \
    -H "Authorization: token ${CODEBERG_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${REPO_NAME}\",\"private\":false,\"description\":\"CFO dashboard for AI token ROI and unit economics\"}"
}

create_github_repo() {
  local owner="$1"
  if ! command -v gh >/dev/null 2>&1; then
    echo "Skip GitHub create for ${owner}: install gh and run gh auth login."
    return 1
  fi
  if ! gh auth status >/dev/null 2>&1; then
    echo "Skip GitHub create for ${owner}: run gh auth login."
    return 1
  fi
  gh repo create "${owner}/${REPO_NAME}" --public \
    --description "CFO dashboard for AI token ROI and unit economics" \
    --source "${ROOT}" --remote "github-${owner//-/_}" 2>/dev/null || \
  gh repo create "${owner}/${REPO_NAME}" --public \
    --description "CFO dashboard for AI token ROI and unit economics"
}

if [[ "${CREATE_REPOS:-}" == "1" ]]; then
  create_codeberg_repo || true
  create_github_repo "${GITHUB_ICOHANGAR_OWNER}" || true
  create_github_repo "${GITHUB_CUBICZAN_OWNER}" || true
fi

echo ""
echo "Remotes:"
git remote -v
echo ""
echo "Push to all destinations:"
echo "  git push -u codeberg main"
echo "  git push -u github-icohangar main"
echo "  git push -u github-cubiczan main"
echo ""
echo "Or: ./scripts/publish-push.sh"
