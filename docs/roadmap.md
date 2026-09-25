# Roadmap and validation boundary

## Executed locally

- MLflow tracking, registry versions/tags, logged artifacts, input/output model
  signatures, and a `champion` alias.
- Five deterministic scikit-learn CPU fixture variants served by independent
  FastAPI runtimes.
- A durable FastAPI release API with SQLite release plans, exact approvals and
  hash-linked audit events.
- SHA-256 artifact verification, offline aggregate and critical-slice gates,
  deterministic canary latency gates, promotion, rollback and stale-plan
  protection.
- Prometheus scraping, clean-room bootstrap, project-scoped cleanup, and a
  Docker end-to-end CI workflow.

## Production hardening

- Require multiple approvers where risk requires it, with approval expiry.
- Replace the local shared-secret identity fixture with an OIDC/JWKS provider.
- Add metrics retention, alert rules, an SBOM and container/artifact supply-chain
  attestations.
- Add richer slice reports plus a release CLI or UI.

## Production / cloud / hardware adapters not executed

- Kubernetes delivery and Argo Rollouts.
- Managed MLflow and object-backed model registry.
- GPU/vLLM/DCGM-backed serving.
- Multi-region serving and enterprise identity.

The CPU fixture models validate the release-control loop only. They are not a
claim of production model quality, GPU performance, cloud deployment, or
large-scale traffic validation.
