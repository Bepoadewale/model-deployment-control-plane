#!/usr/bin/env bash
set -euo pipefail

./scripts/wait-for-url.sh http://localhost:15000/health "MLflow"
./scripts/wait-for-url.sh http://localhost:15080/readyz "release API dependency-aware readiness"
for port in 15101 15102 15103 15104 15105; do
  ./scripts/wait-for-url.sh "http://localhost:${port}/healthz" "runtime ${port}"
done
./scripts/wait-for-url.sh http://localhost:15091/-/ready "Prometheus"
test -s .local/models/registry.json
echo "smoke: local registry, control plane, serving fixtures and Prometheus are healthy"
