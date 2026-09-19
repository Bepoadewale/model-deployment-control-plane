# Model Deployment Control Plane — Agent Guide

Mission: govern model artifact releases using immutable provenance, evaluation, progressive delivery gates, approval, promotion and rollback.

Stack: Python 3.12 release core; future MLflow, serving, kind and rollout controller.

Commands: `PYTHONPATH=control-plane/src python3 -m pytest -q`; add `make` only when targets truly work.

Rules: healthy container is not good model; never call a mock evaluation/deployment real; preserve digest/approval semantics; no secrets/main pushes; tests and factual status updates required.
