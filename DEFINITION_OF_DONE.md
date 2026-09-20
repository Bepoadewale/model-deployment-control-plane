# Definition of Done

# Portfolio Complete — Local-First Scope Gate

- [ ] Local MLflow server registers actual lightweight model artifacts with digest, lineage, aliases/tags, and schema/signature where claimed.
- [ ] Champion/challenger evaluation uses real deterministic fixture models/data with aggregate and slice regression evidence.
- [ ] Champion and candidate serve locally; claimed shadow or weighted canary traffic actually reaches the candidate.
- [ ] A good candidate is promoted to champion through the real release path.
- [ ] A system-healthy but quality-bad candidate is rejected/rolled back; latency regression is also executed if claimed.
- [ ] Tampered artifact is rejected before delivery.
- [ ] Protected promotion approval binds exact release/action; stale release plan and self/unauthorized approval are denied.
- [ ] Release/model metrics or audit evidence run where claimed.
- [ ] Reproducible registry → integrity → evaluation → delivery → online evidence → promote/rollback demo, meaningful tests, and green CI exist.
- [ ] README/status distinguish real local models from unexecuted production registry/Argo/cloud adapters.

## Maturity Levels

- **FOUNDATION:** release decision logic exists.
- **PARTIALLY VALIDATED:** meaningful registry/evaluation integration runs but core delivery is incomplete.
- **LOCAL END-TO-END VALIDATED:** primary release path works with material failure/recovery/observability gaps.
- **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE:** every checked gate is executed; no production rollout claim is inferred.
