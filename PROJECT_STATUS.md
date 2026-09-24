# Project Status

## Current Maturity

PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE

## Executed and Verified

- Local MLflow tracking server and registry registered five real deterministic sklearn model versions with MLflow run IDs, tags, artifacts, signatures and a `champion` alias.
- Five independently running FastAPI model runtimes performed real CPU inference.
- A release API persisted release plans, exact approvals and hash-linked audit events in SQLite.
- A good candidate completed offline aggregate/slice gates, deterministic 10% canary traffic, independent exact-plan approval and MLflow alias promotion.
- A healthy quality-bad candidate rolled back at offline quality gates; a healthy slow candidate received canary traffic then rolled back on p95 latency.
- Artifact tampering was rejected before evaluation; release state survived a release API restart.
- An independently approved older plan was rejected with `409 STALE_RELEASE` after an intervening champion promotion.
- Prometheus scraped live release and runtime metrics.
- Two clean-room cycles were executed: project cleanup → bootstrap → smoke → demo, with the first also executing rollback/tamper/recovery and full Python validation.

## Simulated

- Model data, variants and latency are intentionally deterministic CPU fixtures. They demonstrate release control behavior, not production model quality, GPU performance or real traffic scale.

## Architecture / Contracts Only

- Kubernetes/Argo Rollouts delivery, managed MLflow, cloud registry, production multi-region serving and enterprise identity.

## Known Failures

- None in the validated local scope.

## Current P0 Objective

- Maintain the validated local release path; do not regress clean-room reproducibility.

## Completion Blockers

- None for the declared local-first scope.

## Explicitly Unexecuted Production Adapters

- GPU/vLLM/DCGM, Kubernetes/Argo Rollouts, managed MLflow, cloud object/model registry, enterprise OIDC and multi-region serving.

## Last Validation

- `make clean-local && make bootstrap-local && make smoke && make demo-release && make demo-rollback && make demo-tamper && make demo-recovery && make demo-stale && make verify`: passed (fresh clean-room acceptance cycle).
- `make clean-local && make bootstrap-local && make smoke && make demo-release`: passed (second clean-room cycle).
- `python -m pytest -q`: 7 passed.
- `python -m ruff check control-plane/src tests scripts`: passed.
- Prometheus queries returned live promotion and runtime-request series; the final fresh run observed `model_promotions_total=1` and `model_runtime_requests_total=352`.

## Last Updated

2026-09-24, Week 5 working branch.

## Clean-Room Reproducibility

**Status: VALIDATED.** `make clean-local` removed only Compose resources named for this project plus `.local` and `.venv`; both clean bootstrap cycles recreated local MLflow state, model artifacts, runtime services, release API and Prometheus without undocumented infrastructure.
