# Validation

Run `PYTHONPATH=control-plane/src python3 -m pytest -q` and lint once configured. Any delivery claim must retain versions, services, commands/results, model digest, evaluation inputs, routing configuration, gate result, failure/rollback evidence, and post-rollback verification. Never fabricate validation.
