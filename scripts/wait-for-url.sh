#!/usr/bin/env bash
set -euo pipefail

url="$1"
label="${2:-$url}"
attempts="${3:-45}"
for ((attempt=1; attempt<=attempts; attempt++)); do
  if curl -fsS --max-time 2 "$url" >/dev/null; then
    echo "$label is ready"
    exit 0
  fi
  sleep 2
done
echo "Timed out waiting for $label at $url" >&2
exit 1
