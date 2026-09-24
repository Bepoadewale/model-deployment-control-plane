# Model Deployment Control Plane — Agent Guide

Mission: govern model artifact releases using immutable provenance, evaluation, progressive delivery gates, approval, promotion and rollback.

Stack: Python 3.12, FastAPI, SQLite, MLflow, deterministic scikit-learn CPU fixtures, Docker Compose and Prometheus. Kubernetes/Argo Rollouts remain production adapters.

Commands: `make install`, `make bootstrap-local`, `make smoke`, `make demo-release`, `make demo-rollback`, `make demo-tamper`, `make demo-recovery`, `make demo-stale`, `make verify`, `make clean-local`.

Rules: healthy container is not good model; never call a mock evaluation/deployment real; preserve digest/approval semantics; no secrets/main pushes; tests and factual status updates required.

Completion rule: do not mark **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE** unless the repository-specific gate in `DEFINITION_OF_DONE.md` is backed by executed evidence. Release state classes, fixture metrics, manifests, and mocked tests do not prove model delivery. Registry → integrity → evaluation → serving → promotion/rollback must run locally; cloud rollout adapters remain explicit.

## Clean-room reproducibility

Clean-room reproducibility is a mandatory completion criterion. Do not mark this repository
`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` until a new engineer can reproduce the platform from a
clean project state using documented commands, execute the primary and required failure demos, run
validation, and safely tear down only this project's local resources. Do not infer reproducibility
from an existing developer environment; execute it after project-specific cleanup.
