# Completion Target

PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE

# Current Completion Blockers

None for the local-first scope. Preserve clean-room validation when changing the stack.

# P0 — Required for Portfolio Claim

- [x] Pass the full clean-room reproducibility gate: deterministic bootstrap, smoke, release/failure/recovery demos, safe cleanup and second bootstrap.
- [x] Run local MLflow registry, real artifacts, real serving, promotion and rollback gates.

# P1 — Production Hardening

- Add stronger multi-approver policy and approval expiry.
- Replace local shared-secret fixture identities with OIDC/JWKS integration.
- Add durable metrics retention and alert rules.
- Add a container image supply-chain attestation/SBOM for serving artifacts.

# P2 — Enhancements

- Add a release CLI/UI and richer slice-evaluation reporting.
- Add configurable canary cohorts and bounded online sample windows.

# P3 — Future / Cloud / Hardware

- Kubernetes + Argo Rollouts delivery, managed MLflow/object registry, GPU/vLLM/DCGM and multi-region serving.
