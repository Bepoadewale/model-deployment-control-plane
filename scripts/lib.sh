#!/usr/bin/env bash

# Bounded retry only for a dependency-aware API that has just restarted. Any
# non-503 response is returned immediately so policy/gate failures remain visible.
post_release() {
  local token="$1"
  local candidate="$2"
  local response status attempt
  for attempt in 1 2 3 4 5; do
    response="$(mktemp)"
    status="$(curl -sS -o "$response" -w '%{http_code}' -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' \
      -d "{\"candidate\":\"${candidate}\",\"environment\":\"production\"}" http://localhost:15080/api/v1/releases)"
    if [[ "$status" != "503" ]]; then
      cat "$response"
      rm -f "$response"
      return 0
    fi
    rm -f "$response"
    sleep 2
  done
  echo "release API remained unavailable after bounded retries" >&2
  return 1
}
