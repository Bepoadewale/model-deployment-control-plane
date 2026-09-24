#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"

developer="$(.venv/bin/python scripts/issue_token.py developer-alex --role developer)"
approver="$(.venv/bin/python scripts/issue_token.py approver-sam --role approver)"
headers=(-H "Authorization: Bearer ${developer}" -H 'Content-Type: application/json')

release="$(post_release "$developer" candidate-good)"
release_id="$(jq -r .id <<<"$release")"
plan_hash="$(jq -r .plan_hash <<<"$release")"
test "$(jq -r .state <<<"$release")" = "PROMOTION_PENDING"

self_status="$(curl -sS -o /tmp/modelcp-self-approval.json -w '%{http_code}' "${headers[@]}" -d "{\"plan_hash\":\"${plan_hash}\"}" "http://localhost:15080/api/v1/releases/${release_id}/approvals")"
test "$self_status" = "403"

curl -fsS -H "Authorization: Bearer ${approver}" -H 'Content-Type: application/json' \
  -d "{\"plan_hash\":\"${plan_hash}\"}" "http://localhost:15080/api/v1/releases/${release_id}/approvals" >/dev/null
promoted="$(curl -fsS -X POST -H "Authorization: Bearer ${developer}" "http://localhost:15080/api/v1/releases/${release_id}/promote")"
test "$(jq -r .state <<<"$promoted")" = "PRODUCTION"
echo "demo-release: ${release_id} promoted after exact-plan independent approval; self-approval was denied"
