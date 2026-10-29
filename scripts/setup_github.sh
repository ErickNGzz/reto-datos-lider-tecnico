#!/usr/bin/env bash
# Configura la frontera de aprobación en GitHub. Los environments y la protección de ramas
# no se copian en un fork: córrelo una vez en tu copia (requiere `gh auth login` y ser admin).
#   bash scripts/setup_github.sh [owner/repo]
set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
REVISOR_ID="$(gh api user -q .id)"
REVISOR="$(gh api user -q .login)"
echo "Repo: $REPO · revisor: $REVISOR"

echo "1/4 Habilitar Actions (en un fork vienen apagadas)"
gh api -X PUT "repos/$REPO/actions/permissions" -F enabled=true -f allowed_actions=all > /dev/null

echo "2/4 Environment production: revisor obligatorio, solo desde ramas protegidas"
gh api -X PUT "repos/$REPO/environments/production" --input - > /dev/null <<JSON
{
  "reviewers": [{"type": "User", "id": $REVISOR_ID}],
  "deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}
}
JSON
gh variable set APROBACION_DESTRUCTIVA --env production --body production --repo "$REPO"

echo "3/4 Environment contract-change: revisor obligatorio"
gh api -X PUT "repos/$REPO/environments/contract-change" --input - > /dev/null <<JSON
{
  "reviewers": [{"type": "User", "id": $REVISOR_ID}]
}
JSON

echo "4/4 Proteger main: solo por PR, checks obligatorios, sin force push"
gh api -X PUT "repos/$REPO/branches/main/protection" --input - > /dev/null <<JSON
{
  "required_status_checks": {"strict": true, "contexts": ["idempotencia", "secretos", "aprobacion"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 0},
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Listo. Verifica en https://github.com/$REPO/settings/environments"
