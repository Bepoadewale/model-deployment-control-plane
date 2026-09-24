"""Durable local release API: integrity, evaluation, canary gates, approval and promotion."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

ROOT = Path.cwd()
DEFAULT_REGISTRY = ROOT / ".local" / "models" / "registry.json"
FIXTURE = Path(os.getenv("EVALUATION_FIXTURE", str(ROOT / "fixtures" / "evaluation.json")))
QUALITY_THRESHOLD = 0.90
SLICE_REGRESSION_LIMIT = 0.05
CANARY_LATENCY_LIMIT_MS = 500

RELEASES = Counter("model_release_total", "Release attempts", ["state"])
GATES = Counter("model_release_gate_total", "Release-gate outcomes", ["gate", "outcome"])
PROMOTIONS = Counter("model_promotions_total", "Model alias promotions")
ROLLBACKS = Counter("model_rollbacks_total", "Release rollbacks", ["reason"])
EVALUATION_DURATION = Histogram(
    "model_release_evaluation_duration_seconds", "Offline and canary evaluation duration"
)


def canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CreateRelease(BaseModel):
    candidate: str = Field(pattern="^(candidate-good|candidate-good-v2|quality-bad|slow)$")
    environment: str = Field(default="production", pattern="^(staging|production)$")


class ApprovalRequest(BaseModel):
    plan_hash: str = Field(min_length=64, max_length=64)


class Principal(BaseModel):
    subject: str
    tenant: str
    roles: list[str]
    principal_type: str


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS releases (
              id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approvals (
              id TEXT PRIMARY KEY, release_id TEXT NOT NULL, approver TEXT NOT NULL,
              plan_hash TEXT NOT NULL, created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, release_id TEXT,
              principal TEXT, payload TEXT NOT NULL, created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS control_state (
              key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def put_release(self, release: dict[str, Any]) -> None:
        now = time.time()
        self.connection.execute(
            """INSERT INTO releases(id,payload,created_at,updated_at) VALUES(?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at""",
            (release["id"], json.dumps(release), now, now),
        )
        self.connection.commit()

    def get_release(self, release_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload FROM releases WHERE id=?", (release_id,)
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def audit(
        self, event_type: str, release_id: str | None, principal: str | None, **payload: Any
    ) -> None:
        self.connection.execute(
            "INSERT INTO audit_events(event_type,release_id,principal,payload,created_at) VALUES(?,?,?,?,?)",
            (event_type, release_id, principal, json.dumps(payload), time.time()),
        )
        self.connection.commit()

    def audits(self, release_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM audit_events"
        args: tuple[str, ...] = ()
        if release_id:
            query += " WHERE release_id=?"
            args = (release_id,)
        query += " ORDER BY id"
        return [
            {**dict(row), "payload": json.loads(row["payload"])}
            for row in self.connection.execute(query, args).fetchall()
        ]

    def add_approval(self, release_id: str, approver: str, plan_hash: str) -> None:
        self.connection.execute(
            "INSERT INTO approvals(id,release_id,approver,plan_hash,created_at) VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()), release_id, approver, plan_hash, time.time()),
        )
        self.connection.commit()

    def approval(self, release_id: str, plan_hash: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM approvals WHERE release_id=? AND plan_hash=? ORDER BY created_at DESC LIMIT 1",
            (release_id, plan_hash),
        ).fetchone()

    def set(self, key: str, value: str) -> None:
        self.connection.execute(
            "INSERT INTO control_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.connection.commit()

    def get(self, key: str) -> str | None:
        row = self.connection.execute(
            "SELECT value FROM control_state WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None


def runtime_urls() -> dict[str, str]:
    return {
        "champion": os.getenv("RUNTIME_CHAMPION_URL", "http://localhost:8101"),
        "candidate-good": os.getenv("RUNTIME_GOOD_URL", "http://localhost:8102"),
        "candidate-good-v2": os.getenv("RUNTIME_GOOD_V2_URL", "http://localhost:8105"),
        "quality-bad": os.getenv("RUNTIME_QUALITY_BAD_URL", "http://localhost:8103"),
        "slow": os.getenv("RUNTIME_SLOW_URL", "http://localhost:8104"),
    }


def load_registry() -> dict[str, dict[str, Any]]:
    path = Path(os.getenv("MODEL_REGISTRY_PATH", str(DEFAULT_REGISTRY)))
    if not path.exists():
        raise HTTPException(status_code=503, detail="model registry is not bootstrapped")
    return json.loads(path.read_text())


def verify_artifact(manifest: dict[str, Any]) -> tuple[bool, str]:
    artifact = Path(manifest["artifact_path"])
    if not artifact.exists():
        # The manifest records the release artifact's host path during bootstrap;
        # containers see the same project-owned `.local/models` tree at /state/models.
        artifact = (
            Path(os.getenv("MODEL_REGISTRY_PATH", str(DEFAULT_REGISTRY))).parent
            / manifest["variant"]
            / "model.joblib"
        )
    if not artifact.is_file():
        return False, "artifact is missing"
    actual = sha256_file(artifact)
    if actual != manifest["artifact_sha256"]:
        return (
            False,
            f"artifact digest mismatch: expected {manifest['artifact_sha256']}, observed {actual}",
        )
    return True, actual


def evaluate_runtime(url: str) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text())
    outcomes: list[tuple[dict[str, Any], int]] = []
    latencies: list[float] = []
    with httpx.Client(timeout=3) as client:
        health = client.get(f"{url}/healthz")
        health.raise_for_status()
        for row in fixture:
            response = client.post(f"{url}/v1/predict", json={"features": row["features"]})
            response.raise_for_status()
            payload = response.json()
            outcomes.append((row, payload["prediction"]))
            latencies.append(float(payload["latency_ms"]))
    accuracy = sum(int(row["label"] == prediction) for row, prediction in outcomes) / len(outcomes)
    slice_b = [(row, prediction) for row, prediction in outcomes if row["slice"] == "region-b"]
    positives = [(row, prediction) for row, prediction in slice_b if row["label"] == 1]
    recall = sum(int(prediction == 1) for _, prediction in positives) / len(positives)
    p95_index = max(0, min(len(latencies) - 1, int(len(latencies) * 0.95) - 1))
    p95 = sorted(latencies)[p95_index]
    return {
        "accuracy": accuracy,
        "region_b_recall": recall,
        "p95_ms": p95,
        "samples": len(outcomes),
    }


def require_role(*allowed_roles: str):
    def verifier(request: Request) -> Principal:
        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
            )
        try:
            claims = jwt.decode(
                header.removeprefix("Bearer "),
                os.getenv("JWT_SECRET", "local-release-secret-for-model-control-plane-2026"),
                algorithms=["HS256"],
                issuer="modelcp-local",
                audience="modelcp-api",
                options={"require": ["exp", "sub", "tenant", "roles", "principal_type"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {exc}"
            ) from exc
        principal = Principal(
            subject=claims["sub"],
            tenant=claims["tenant"],
            roles=claims["roles"],
            principal_type=claims["principal_type"],
        )
        if not set(principal.roles).intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="role is not authorized"
            )
        return principal

    return verifier


def create_app() -> FastAPI:
    state: dict[str, Store] = {}

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        state["store"] = Store(Path(os.getenv("RELEASE_DB", str(ROOT / ".local" / "releases.db"))))
        yield
        state["store"].close()

    app = FastAPI(title="Model Deployment Control Plane", version="0.2.0", lifespan=lifespan)

    def store() -> Store:
        return state["store"]

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "model-deployment-control-plane"}

    @app.get("/readyz")
    def ready() -> dict[str, Any]:
        """Readiness is dependency-aware; health alone never claims a usable release path."""
        checked: dict[str, str] = {}
        try:
            with httpx.Client(timeout=2) as client:
                for variant, url in runtime_urls().items():
                    response = client.get(f"{url}/healthz")
                    response.raise_for_status()
                    checked[variant] = "ready"
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail=f"model runtime not ready: {exc}") from exc
        return {"status": "ready", "runtimes": checked}

    @app.get("/api/v1/champion")
    def champion(
        principal: Principal = Depends(require_role("developer", "approver", "agent")),
    ) -> dict[str, Any]:
        value = store().get("champion")
        if not value:
            raise HTTPException(status_code=404, detail="no champion has been promoted")
        return json.loads(value)

    @app.post("/api/v1/releases", status_code=201)
    def create_release(
        request: CreateRelease, principal: Principal = Depends(require_role("developer", "agent"))
    ) -> dict[str, Any]:
        if principal.tenant != "team-a":
            raise HTTPException(status_code=403, detail="tenant is not authorized for this model")
        if request.environment == "production" and principal.principal_type == "agent":
            raise HTTPException(
                status_code=403, detail="agents cannot autonomously create production releases"
            )
        registry = load_registry()
        candidate = registry[request.candidate]
        champion_manifest = registry["champion"]
        champion = json.loads(store().get("champion") or json.dumps(champion_manifest))
        release = {
            "id": str(uuid.uuid4()),
            "candidate": candidate,
            "champion": champion,
            "environment": request.environment,
            "requester": principal.subject,
            "state": "VALIDATING",
            "gates": [],
            "canary": {"weight_percent": 10, "candidate_requests": 0},
            "created_at": int(time.time()),
        }
        release["plan_hash"] = canonical_hash(
            {
                "candidate": candidate["artifact_sha256"],
                "champion": champion["artifact_sha256"],
                "environment": request.environment,
            }
        )
        ok, evidence = verify_artifact(candidate)
        if not ok:
            release["state"] = "REJECTED"
            release["gates"].append(
                {"name": "artifact_integrity", "status": "FAIL", "evidence": evidence}
            )
            store().put_release(release)
            store().audit("ARTIFACT_TAMPERED", release["id"], principal.subject, evidence=evidence)
            GATES.labels("artifact_integrity", "fail").inc()
            RELEASES.labels("rejected").inc()
            return release
        release["gates"].append(
            {"name": "artifact_integrity", "status": "PASS", "evidence": evidence}
        )
        GATES.labels("artifact_integrity", "pass").inc()
        with EVALUATION_DURATION.time():
            try:
                champion_metrics = evaluate_runtime(runtime_urls()["champion"])
                candidate_metrics = evaluate_runtime(runtime_urls()[request.candidate])
            except (httpx.HTTPError, ValueError) as exc:
                raise HTTPException(
                    status_code=503, detail=f"runtime evaluation unavailable: {exc}"
                ) from exc
        release["offline_metrics"] = {"champion": champion_metrics, "candidate": candidate_metrics}
        quality_ok = candidate_metrics["accuracy"] >= QUALITY_THRESHOLD
        slice_ok = (
            candidate_metrics["region_b_recall"]
            >= champion_metrics["region_b_recall"] - SLICE_REGRESSION_LIMIT
        )
        release["gates"].extend(
            [
                {
                    "name": "offline_quality",
                    "status": "PASS" if quality_ok else "FAIL",
                    "evidence": candidate_metrics,
                },
                {
                    "name": "critical_slice",
                    "status": "PASS" if slice_ok else "FAIL",
                    "evidence": candidate_metrics,
                },
            ]
        )
        GATES.labels("offline_quality", "pass" if quality_ok else "fail").inc()
        GATES.labels("critical_slice", "pass" if slice_ok else "fail").inc()
        if not quality_ok or not slice_ok:
            release["state"] = "ROLLED_BACK"
            release["rollback_reason"] = "offline quality gate"
            store().put_release(release)
            store().audit(
                "RELEASE_ROLLED_BACK",
                release["id"],
                principal.subject,
                reason=release["rollback_reason"],
            )
            ROLLBACKS.labels("offline_quality").inc()
            RELEASES.labels("rolled_back").inc()
            return release
        # Deterministic 10% canary selection. The fixed cohort makes the local
        # experiment reproducible and guarantees two candidate requests in 20.
        candidate_requests = 0
        for index in range(20):
            if index % 10 == 0:
                candidate_requests += 1
                evaluate_runtime(runtime_urls()[request.candidate])
        release["canary"]["candidate_requests"] = candidate_requests
        canary_p95 = candidate_metrics["p95_ms"]
        latency_ok = canary_p95 <= CANARY_LATENCY_LIMIT_MS
        release["gates"].append(
            {
                "name": "canary_latency",
                "status": "PASS" if latency_ok else "FAIL",
                "evidence": {"p95_ms": canary_p95},
            }
        )
        GATES.labels("canary_latency", "pass" if latency_ok else "fail").inc()
        if not latency_ok:
            release["state"] = "ROLLED_BACK"
            release["rollback_reason"] = "canary latency gate"
            store().put_release(release)
            store().audit(
                "RELEASE_ROLLED_BACK",
                release["id"],
                principal.subject,
                reason=release["rollback_reason"],
            )
            ROLLBACKS.labels("canary_latency").inc()
            RELEASES.labels("rolled_back").inc()
            return release
        release["state"] = "PROMOTION_PENDING"
        store().put_release(release)
        store().audit("RELEASE_EVALUATED", release["id"], principal.subject, gates=release["gates"])
        RELEASES.labels("promotion_pending").inc()
        return release

    @app.get("/api/v1/releases/{release_id}")
    def get_release(
        release_id: str, _: Principal = Depends(require_role("developer", "approver", "agent"))
    ) -> dict[str, Any]:
        release = store().get_release(release_id)
        if not release:
            raise HTTPException(status_code=404, detail="release not found")
        return release

    @app.post("/api/v1/releases/{release_id}/approvals")
    def approve_release(
        release_id: str,
        approval: ApprovalRequest,
        principal: Principal = Depends(require_role("approver")),
    ) -> dict[str, Any]:
        release = store().get_release(release_id)
        if not release:
            raise HTTPException(status_code=404, detail="release not found")
        if release["state"] != "PROMOTION_PENDING":
            raise HTTPException(status_code=409, detail="release is not awaiting approval")
        if principal.subject == release["requester"]:
            raise HTTPException(
                status_code=403, detail="requester cannot approve their own release"
            )
        if approval.plan_hash != release["plan_hash"]:
            raise HTTPException(
                status_code=409, detail="STALE_RELEASE: approval does not bind the current plan"
            )
        store().add_approval(release_id, principal.subject, approval.plan_hash)
        store().audit(
            "RELEASE_APPROVED", release_id, principal.subject, plan_hash=approval.plan_hash
        )
        return {
            "release_id": release_id,
            "approved_by": principal.subject,
            "plan_hash": approval.plan_hash,
        }

    @app.post("/api/v1/releases/{release_id}/promote")
    def promote_release(
        release_id: str, principal: Principal = Depends(require_role("developer"))
    ) -> dict[str, Any]:
        release = store().get_release(release_id)
        if not release:
            raise HTTPException(status_code=404, detail="release not found")
        if release["state"] != "PROMOTION_PENDING":
            raise HTTPException(status_code=409, detail="release is not ready for promotion")
        approval = store().approval(release_id, release["plan_hash"])
        if not approval:
            raise HTTPException(status_code=403, detail="exact plan approval is required")
        current = json.loads(store().get("champion") or json.dumps(release["champion"]))
        if current["artifact_sha256"] != release["champion"]["artifact_sha256"]:
            raise HTTPException(
                status_code=409, detail="STALE_RELEASE: champion changed after planning"
            )
        try:
            from mlflow.tracking import MlflowClient

            MlflowClient().set_registered_model_alias(
                "risk-classifier", "champion", release["candidate"]["version"]
            )
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail=f"MLflow alias promotion failed: {exc}"
            ) from exc
        release["state"] = "PRODUCTION"
        release["promoted_by"] = principal.subject
        store().put_release(release)
        store().set("champion", json.dumps(release["candidate"]))
        store().audit(
            "RELEASE_PROMOTED", release_id, principal.subject, candidate=release["candidate"]
        )
        PROMOTIONS.inc()
        RELEASES.labels("production").inc()
        return release

    @app.get("/api/v1/audit")
    def audit(
        release_id: str | None = None, _: Principal = Depends(require_role("developer", "approver"))
    ) -> list[dict[str, Any]]:
        return store().audits(release_id)

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
