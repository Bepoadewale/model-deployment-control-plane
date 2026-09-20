# Model Deployment Control Plane — Agent Guide

Mission: govern model artifact releases using immutable provenance, evaluation, progressive delivery gates, approval, promotion and rollback.

Stack: Python 3.12 release core; future MLflow, serving, kind and rollout controller.

Commands: `PYTHONPATH=control-plane/src python3 -m pytest -q`; add `make` only when targets truly work.

Rules: healthy container is not good model; never call a mock evaluation/deployment real; preserve digest/approval semantics; no secrets/main pushes; tests and factual status updates required.

Completion rule: do not mark **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE** unless the repository-specific gate in `DEFINITION_OF_DONE.md` is backed by executed evidence. Release state classes, fixture metrics, manifests, and mocked tests do not prove model delivery. Registry → integrity → evaluation → serving → promotion/rollback must run locally; cloud rollout adapters remain explicit.

## Clean-room reproducibility

Clean-room reproducibility is a mandatory completion criterion. Do not mark this repository
`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` until a new engineer can reproduce the platform from a
clean project state using documented commands, execute the primary and required failure demos, run
validation, and safely tear down only this project's local resources. Do not infer reproducibility
from an existing developer environment; execute it after project-specific cleanup.
