# P0 — Required for Portfolio Claim

- Start local MLflow registry and register two tiny model artifacts with digest/lineage/schema.
- Run deterministic champion/challenger evaluation against real data fixtures.
- Deploy champion/candidate locally and implement shadow or weighted canary route.
- Measure quality/latency gates; promote a good candidate.
- Exercise quality or latency regression rollback and verify prior model restored.

# P1 — Production Hardening

- Persistent release state, approval/audit API, reproducible model packaging and alerting.

# P2 — Enhancements

- UI/CLI and richer evaluation-slice reporting.

# P3 — Future / Cloud / Hardware

- Argo Rollouts, production registry and multi-region serving.
