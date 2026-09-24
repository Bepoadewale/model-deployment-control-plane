#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"

artifact=.local/models/candidate-good/model.joblib
backup="$(mktemp)"
cp "$artifact" "$backup"
trap 'mv "$backup" "$artifact"' EXIT
printf 'tampered' >> "$artifact"
developer="$(.venv/bin/python scripts/issue_token.py developer-alex --role developer)"
response="$(post_release "$developer" candidate-good)"
test "$(jq -r .state <<<"$response")" = "REJECTED"
test "$(jq -r '.gates[] | select(.name=="artifact_integrity") | .status' <<<"$response")" = "FAIL"
echo "demo-tamper: modified signed/referenced artifact was rejected before deployment"
