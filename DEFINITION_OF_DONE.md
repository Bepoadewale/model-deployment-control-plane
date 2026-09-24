# Definition of Done

## Portfolio Complete — Local-First Scope Gate

- [x] Local MLflow server registers lightweight model artifacts with digest, lineage, aliases/tags and signature metadata.
- [x] Champion/challenger evaluation uses real deterministic fixture models/data with aggregate and critical-slice evidence.
- [x] Champion and candidates serve in independent local processes; deterministic canary traffic reaches the candidate.
- [x] A good candidate is promoted to champion through the real release path.
- [x] Healthy quality-bad and latency-regressed candidates are rejected/rolled back without changing the champion.
- [x] A tampered artifact is rejected before delivery.
- [x] Exact-plan independent approval and self/unauthorized approval denial execute; a live stale-release demo rejects an older approved plan after a newer champion promotion.
- [x] Persistent audit/release state and Prometheus release/runtime metrics execute locally.
- [x] Meaningful unit tests and a Docker E2E CI job exist.
- [x] README/status distinguish real local models from unexecuted production adapters.

## Clean-Room Reproducibility Gate

- [x] Clean project state → bootstrap → smoke → successful release demo executed.
- [x] Important failure/security demos (quality/latency rollback and tamper rejection) executed.
- [x] Project-scoped cleanup removed only this project's Compose resources, `.local` and `.venv`.
- [x] Second clean bootstrap and successful release demo executed.
- [x] `docs/VALIDATION.md` and README commands reflect executed evidence.

## Explicit boundary

This completion level validates the local release-control architecture. It does not claim real GPU serving, Kubernetes/Argo delivery, a managed model registry, enterprise identity or cloud production validation.
