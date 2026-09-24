#!/usr/bin/env bash
set -euo pipefail

developer="$(.venv/bin/python scripts/issue_token.py developer-alex --role developer)"
headers=(-H "Authorization: Bearer ${developer}" -H 'Content-Type: application/json')
release="$(curl -fsS "${headers[@]}" -d '{"candidate":"candidate-good","environment":"staging"}' http://localhost:15080/api/v1/releases)"
release_id="$(jq -r .id <<<"$release")"
docker compose restart release-api >/dev/null
./scripts/wait-for-url.sh http://localhost:15080/readyz "release API after restart"
restored="$(curl -fsS -H "Authorization: Bearer ${developer}" "http://localhost:15080/api/v1/releases/${release_id}")"
test "$(jq -r .id <<<"$restored")" = "$release_id"
echo "demo-recovery: persisted release ${release_id} survived a release-api restart"
