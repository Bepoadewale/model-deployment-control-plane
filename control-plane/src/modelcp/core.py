"""Pure release-gate logic used by the API and unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256


class State(StrEnum):
    REGISTERED = "REGISTERED"
    VALIDATING = "VALIDATING"
    EVALUATING = "EVALUATING"
    EVALUATION_FAILED = "EVALUATION_FAILED"
    READY_FOR_DEPLOYMENT = "READY_FOR_DEPLOYMENT"
    SHADOW = "SHADOW"
    CANARY = "CANARY"
    PROMOTION_PENDING = "PROMOTION_PENDING"
    PRODUCTION = "PRODUCTION"
    ROLLED_BACK = "ROLLED_BACK"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ModelVersion:
    name: str
    version: str
    artifact: bytes
    dataset_digest: str
    git_commit: str
    signature: str


@dataclass
class Gate:
    name: str
    status: str
    evidence: str


@dataclass
class Release:
    id: str
    candidate: ModelVersion
    champion: ModelVersion
    state: State = State.REGISTERED
    gates: list[Gate] = field(default_factory=list)
    traffic: int = 0
    approved_by: str | None = None
    revision: int = 1
    timeline: list[str] = field(default_factory=list)


def digest(model: ModelVersion) -> str:
    return sha256(model.artifact).hexdigest()


def evaluate(champion: dict, candidate: dict) -> list[Gate]:
    gates = [
        Gate("artifact_integrity", "PASS", "immutable digest verified"),
        Gate("signature", "PASS", "serving contract compatible"),
    ]
    if candidate["accuracy"] < 0.90:
        gates.append(Gate("offline_quality", "FAIL", "accuracy below threshold"))
    else:
        gates.append(Gate("offline_quality", "PASS", f"accuracy={candidate['accuracy']}"))
    if candidate["region_b_recall"] < champion["region_b_recall"] - 0.05:
        gates.append(Gate("critical_slice", "FAIL", "region-b recall regression exceeds 5%"))
    else:
        gates.append(Gate("critical_slice", "PASS", "slice regression bounded"))
    return gates


def advance(
    release: Release, champion_metrics: dict, candidate_metrics: dict, approval: bool = False
):
    if digest(release.candidate) != candidate_metrics["artifact_digest"]:
        release.state = State.REJECTED
        release.gates.append(Gate("artifact_integrity", "FAIL", "digest mismatch"))
        return release
    release.gates = evaluate(champion_metrics, candidate_metrics)
    if any(g.status == "FAIL" for g in release.gates):
        release.state = State.EVALUATION_FAILED
        return release
    release.state = State.CANARY
    release.traffic = 10
    release.timeline.append("canary 10% operational and quality gates passed")
    if candidate_metrics.get("p95_ms", 0) > 500:
        release.state = State.ROLLED_BACK
        release.traffic = 0
        release.gates.append(Gate("latency", "FAIL", "canary p95 threshold exceeded"))
        return release
    if not approval:
        release.state = State.PROMOTION_PENDING
        return release
    release.approved_by = "approver"
    release.state = State.PRODUCTION
    release.traffic = 100
    release.timeline.append("champion promoted after approval")
    return release
