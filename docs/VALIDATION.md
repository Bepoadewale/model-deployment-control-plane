# Validation

## Local validation commands

```bash
make install
make bootstrap-local
make smoke
make demo-release
make demo-rollback
make demo-tamper
make demo-recovery
make demo-stale
make verify
```

`bootstrap-local` creates project-owned MLflow SQLite/artifact state under `.local/mlflow`, registers five deterministic sklearn variants, starts five model runtimes, the FastAPI release API and Prometheus. It waits on bounded health/readiness probes rather than arbitrary sleeps.

## Expected evidence

- `demo-release`: candidate-good completes offline evaluation and a deterministic 10% canary; a requester self-approval receives `403`; an independent approver binds the plan hash; promotion changes the local MLflow `champion` alias.
- `demo-rollback`: a healthy `quality-bad` runtime fails offline quality; a healthy `slow` runtime receives canary traffic then fails the p95 gate; both preserve the champion.
- `demo-tamper`: a byte-modified referenced artifact is rejected before activation.
- `demo-recovery`: SQLite release state remains retrievable after the release API is restarted.
- `demo-stale`: an older approved plan cannot overwrite a champion promoted by an intervening release; the API returns `409 STALE_RELEASE`.
- Prometheus scrapes release and runtime metrics at `http://localhost:15091`.

## Clean-room evidence

Date: 2026-09-24
Working branch: `codex/week-05-model-deployment-control-plane`
Environment: macOS on Apple Silicon, Python 3.12.12, Docker Compose v2.40.3-desktop.1, MLflow 3.16.1.

Starting state: `make clean-local` removed only the `model-deployment-control-plane` Compose stack, its network/volumes, `.local` state and `.venv`. No shared Docker prune or Kubernetes deletion was used.

First clean-room acceptance execution:

```bash
make clean-local
make bootstrap-local
make smoke
make demo-release
make demo-rollback
make demo-tamper
make demo-recovery
make demo-stale
make verify
```

Results: MLflow, the API, five runtimes and Prometheus became ready. The good candidate was promoted after independent approval; quality and latency failures rolled back; a modified artifact was rejected; SQLite state survived an API restart; an older plan was rejected with `409 STALE_RELEASE`; Ruff passed; pytest reported `7 passed`.

Second clean-room execution:

```bash
make clean-local
make bootstrap-local
make smoke
make demo-release
```

The second bootstrap recreated MLflow state, artifacts and services without relying on the first cycle. Prometheus observed release and runtime requests during the runs. Final project-scoped cleanup was run with `make clean-local`; no project-owned containers, network, `.local` state or `.venv` remained.
