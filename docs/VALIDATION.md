# Validation

Run `PYTHONPATH=control-plane/src python3 -m pytest -q` and lint once configured. Any delivery claim must retain versions, services, commands/results, model digest, evaluation inputs, routing configuration, gate result, failure/rollback evidence, and post-rollback verification. Never fabricate validation.

## Clean-Room Validation

Do not populate this section until executed. Record: date, commit SHA, OS/environment, Docker/kind/Kubernetes and key dependency versions where applicable; clean starting state; exact install/bootstrap/smoke/demo/failure/validation/cleanup commands; observed results; post-cleanup absence verification; and the second-bootstrap result. No prior local state or fabricated evidence is acceptable.
