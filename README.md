# Model Deployment Control Plane

A local-first release control plane for model artifacts. It proves that a container being healthy is not enough to promote a model: provenance, offline quality, critical slices, canary latency and an independent approval all gate the champion alias.

```text
MLflow registry → digest/provenance → real offline evaluation → deterministic canary
→ exact-plan independent approval → champion alias promotion
                                      ↘ quality/latency/tamper failure → rollback/rejection
```

## What it allows—and prevents

- A developer can submit a candidate for a production release plan.
- A separate approver must approve the exact immutable plan hash before promotion.
- The requester cannot approve their own release; agents cannot autonomously create a production release.
- The control plane rejects a modified artifact before evaluation, rejects a system-healthy model with poor quality, and rolls back a slow canary without changing the champion.
- A new release cannot promote if the champion changed after planning (`STALE_RELEASE`).

## Executed local stack

| Capability | Status | Evidence |
| --- | --- | --- |
| MLflow registry, versions, tags, model schema signature, real fixture metrics and champion alias | ✅ Executed locally | `make bootstrap-local` |
| Deterministic scikit-learn models and HTTP serving | ✅ Executed locally | five FastAPI runtime containers |
| Digest verification and tamper rejection | ✅ Executed locally | `make demo-tamper` |
| Offline aggregate/slice evaluation | ✅ Executed locally | `make demo-rollback` |
| Deterministic 10% canary and latency rollback | ✅ Executed locally | `make demo-rollback` |
| Durable release/approval/audit state | ✅ Executed locally | SQLite + `make demo-recovery` |
| Exact-plan independent approval | ✅ Executed locally | `make demo-release` |
| Stale-plan protection | ✅ Executed locally | `make demo-stale` returns `409 STALE_RELEASE` |
| Prometheus metrics | ✅ Executed locally | `http://localhost:15091` |
| GPU, Kubernetes, Argo Rollouts and cloud registry | 📋 Production adapters | not executed or claimed |

## Run from a clean project state

Prerequisites: Docker Desktop, Docker Compose, Python 3.12 and `curl`/`jq`.

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
make clean-local
```

Local endpoints: MLflow `http://localhost:15000`, release API `http://localhost:15080/docs`, Prometheus `http://localhost:15091`.

`make clean-local` removes only this Compose project, its `.local` state and its Python virtual environment; it does not prune shared Docker resources. See [validation evidence](docs/VALIDATION.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md).

## Deliberate local fixture limits

The fixture models are CPU-only deterministic classifiers. Their accuracy and latency values validate release-control behavior—not model quality or production performance. Real GPU hardware, Kubernetes/Argo Rollouts, managed MLflow, enterprise identity and cloud model registries are intentionally not represented as executed.
