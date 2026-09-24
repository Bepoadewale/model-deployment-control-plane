SHELL := /usr/bin/env bash
VENV := .venv
PYTHON := $(VENV)/bin/python
COMPOSE := LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) docker compose

.PHONY: install bootstrap-local smoke demo-release demo-rollback demo-tamper demo-recovery demo-stale verify status clean-local

install:
	@if ! test -x $(PYTHON) || ! $(PYTHON) -c 'import mlflow, pytest, ruff' >/dev/null 2>&1; then \
		rm -rf $(VENV); \
		python3.12 -m venv $(VENV); \
		$(PYTHON) -m pip install --disable-pip-version-check --quiet --upgrade pip; \
		$(PYTHON) -m pip install --disable-pip-version-check --quiet -e '.[dev]'; \
	fi

bootstrap-local: install
	mkdir -p .local/mlflow
	$(COMPOSE) up -d mlflow release-api
	./scripts/wait-for-url.sh http://localhost:15000/health "MLflow"
	MLFLOW_TRACKING_URI=http://localhost:15000 $(PYTHON) scripts/register_models.py
	$(COMPOSE) up -d runtime-champion runtime-good runtime-good-v2 runtime-quality-bad runtime-slow prometheus
	$(MAKE) smoke

smoke:
	./scripts/smoke.sh

demo-release:
	./scripts/demo-release.sh

demo-rollback:
	./scripts/demo-rollback.sh

demo-tamper:
	./scripts/demo-tamper.sh

demo-recovery:
	./scripts/demo-recovery.sh

demo-stale:
	./scripts/demo-stale.sh

verify: install
	$(PYTHON) -m ruff check control-plane/src tests scripts
	$(PYTHON) -m pytest -q

status:
	$(COMPOSE) ps
	curl -fsS http://localhost:15080/healthz
	curl -fsS http://localhost:15000/health

clean-local:
	$(COMPOSE) down --volumes --remove-orphans
	rm -rf .local $(VENV)
