#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"

developer="$(.venv/bin/python scripts/issue_token.py developer-alex --role developer)"
headers=(-H "Authorization: Bearer ${developer}" -H 'Content-Type: application/json')

quality="$(post_release "$developer" quality-bad)"
test "$(jq -r .state <<<"$quality")" = "ROLLED_BACK"
test "$(jq -r .rollback_reason <<<"$quality")" = "offline quality gate"

slow="$(post_release "$developer" slow)"
test "$(jq -r .state <<<"$slow")" = "ROLLED_BACK"
test "$(jq -r .rollback_reason <<<"$slow")" = "canary latency gate"
test "$(jq -r .canary.candidate_requests <<<"$slow")" -gt 0
echo "demo-rollback: a healthy-but-low-quality candidate and a high-latency canary were rolled back"
