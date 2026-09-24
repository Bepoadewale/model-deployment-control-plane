#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"

developer="$(.venv/bin/python scripts/issue_token.py developer-alex --role developer)"
approver="$(.venv/bin/python scripts/issue_token.py approver-sam --role approver)"

# Plan A is intentionally held while the independently approved plan B makes
# candidate-good-v2 the champion. Plan A must not overwrite that newer state.
old="$(post_release "$developer" candidate-good)"
old_id="$(jq -r .id <<<"$old")"
old_hash="$(jq -r .plan_hash <<<"$old")"
test "$(jq -r .state <<<"$old")" = "PROMOTION_PENDING"

new="$(post_release "$developer" candidate-good-v2)"
new_id="$(jq -r .id <<<"$new")"
new_hash="$(jq -r .plan_hash <<<"$new")"
test "$(jq -r .state <<<"$new")" = "PROMOTION_PENDING"

curl -fsS -H "Authorization: Bearer ${approver}" -H 'Content-Type: application/json' \
  -d "{\"plan_hash\":\"${new_hash}\"}" "http://localhost:15080/api/v1/releases/${new_id}/approvals" >/dev/null
curl -fsS -X POST -H "Authorization: Bearer ${developer}" \
  "http://localhost:15080/api/v1/releases/${new_id}/promote" >/dev/null

curl -fsS -H "Authorization: Bearer ${approver}" -H 'Content-Type: application/json' \
  -d "{\"plan_hash\":\"${old_hash}\"}" "http://localhost:15080/api/v1/releases/${old_id}/approvals" >/dev/null
response="$(mktemp)"
status="$(curl -sS -o "$response" -w '%{http_code}' -X POST -H "Authorization: Bearer ${developer}" \
  "http://localhost:15080/api/v1/releases/${old_id}/promote")"
test "$status" = "409"
jq -e '.detail | contains("STALE_RELEASE")' "$response" >/dev/null
rm -f "$response"
echo "demo-stale: an older exact-plan approval was rejected after a newer champion promotion"
