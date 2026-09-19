# Model Deployment Control Plane

A governed release core for moving model artifacts through provenance, offline/slice evaluation, progressive delivery gates, approval, promotion and verified rollback decisions. A healthy service is not assumed to be a good model.

```mermaid
flowchart LR
R[Registry artifact]-->P[Digest + provenance]
P-->E[Offline and slice evaluation]
E-->S[Shadow / canary plan]
S-->G[Operational + quality gates]
G-->A[Approval]
A-->X[Promote or roll back]
```

The executable local core uses two tiny in-memory fixture artifacts. It proves: immutable digest failure blocks release; slice regression blocks aggregate improvement; latency regression rolls back; successful production promotion requires approval.

```bash
python -m pip install -e '.[dev]'
PYTHONPATH=control-plane/src pytest -q
```

MLflow, kind, serving, shadow routing, Argo Rollouts and real canary validation are planned integrations, not yet claimed as implemented.
