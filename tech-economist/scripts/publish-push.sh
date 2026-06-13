#!/usr/bin/env bash
# Push tech-economist to Codeberg and both GitHub owners.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

for remote in codeberg github-icohangar github-cubiczan; do
  echo "=== Pushing to ${remote} ==="
  git push -u "${remote}" main
done

echo "Done. Published to Codeberg, icohangar-ops, and cubiczan."
