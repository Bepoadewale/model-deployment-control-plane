#!/usr/bin/env python3
"""Create real deterministic sklearn artifacts and register them in local MLflow."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
MODELS = LOCAL / "models"
FIXTURE = ROOT / "fixtures" / "evaluation.json"
MODEL_NAME = "risk-classifier"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wait_ready(client: MlflowClient, name: str, version: str) -> None:
    for _ in range(30):
        result = client.get_model_version(name, version)
        if result.status == "READY":
            return
        time.sleep(0.5)
    raise RuntimeError(f"MLflow model {name}:{version} was not ready")


def make_model(variant: str):
    features = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]] * 4
    labels = [0, 0, 0, 1] * 4
    if variant == "quality-bad":
        return DummyClassifier(strategy="constant", constant=0).fit(features, labels)
    # The second good candidate has equivalent fixture quality but a distinct
    # serialized artifact. It lets the local demo prove stale-plan protection
    # against a real intervening champion change.
    regularization = 1000 if variant != "candidate-good-v2" else 100
    return LogisticRegression(C=regularization, random_state=7, max_iter=500).fit(features, labels)


def evaluate_fixture(model, data: list[dict[str, object]]) -> dict[str, float]:
    """Calculate the MLflow run metrics from the real local evaluation fixture."""
    features = [row["features"] for row in data]
    started = time.perf_counter()
    predictions = model.predict(features)
    elapsed_ms = (time.perf_counter() - started) * 1000
    labels = [int(row["label"]) for row in data]
    accuracy = sum(int(actual == prediction) for actual, prediction in zip(labels, predictions)) / len(
        labels
    )
    region_b = [
        (int(row["label"]), int(prediction))
        for row, prediction in zip(data, predictions)
        if row["slice"] == "region-b"
    ]
    positives = [(actual, prediction) for actual, prediction in region_b if actual == 1]
    recall = sum(int(prediction == 1) for _, prediction in positives) / len(positives)
    return {
        "fixture_accuracy": accuracy,
        "region_b_recall": recall,
        "fixture_batch_inference_ms": elapsed_ms,
    }


def register(variant: str, delay_ms: int) -> dict[str, object]:
    print(f"registering {variant}", flush=True)
    model = make_model(variant)
    destination = MODELS / variant
    destination.mkdir(parents=True, exist_ok=True)
    artifact = destination / "model.joblib"
    joblib.dump(model, artifact)
    artifact_digest = sha256_file(artifact)
    fixture_digest = sha256_file(FIXTURE)
    data = json.loads(FIXTURE.read_text())
    sample = [row["features"] for row in data]
    predictions = model.predict(sample)
    signature = infer_signature(sample, predictions)
    evaluation = evaluate_fixture(model, data)
    model_parameters = model.get_params()

    with mlflow.start_run(run_name=f"bootstrap-{variant}") as run:
        print(f"logging {variant}", flush=True)
        mlflow.set_tags(
            {
                "release.variant": variant,
                "source.git_commit": "local-fixture",
                "data.digest": fixture_digest,
                "artifact.sha256": artifact_digest,
            }
        )
        mlflow.log_params(
            {
                "variant": variant,
                "model_type": type(model).__name__,
                "feature_count": len(sample[0]),
                "fixture_rows": len(data),
                "training_rows": 16,
                "regularization_c": model_parameters.get("C", "not-applicable"),
                "max_iterations": model_parameters.get("max_iter", "not-applicable"),
                "configured_runtime_delay_ms": delay_ms,
            }
        )
        mlflow.log_metrics(
            {
                **evaluation,
                "artifact_size_bytes": float(artifact.stat().st_size),
            }
        )
        mlflow.log_artifact(str(artifact), artifact_path="serving")
        info = mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            signature=signature,
            input_example=sample[:2],
        )
        print(f"registering MLflow version for {variant}", flush=True)
        registered = mlflow.register_model(info.model_uri, MODEL_NAME)
        client = MlflowClient()
        wait_ready(client, MODEL_NAME, registered.version)
        client.set_model_version_tag(MODEL_NAME, registered.version, "release.variant", variant)
        client.set_model_version_tag(
            MODEL_NAME, registered.version, "artifact.sha256", artifact_digest
        )
        client.set_model_version_tag(MODEL_NAME, registered.version, "data.digest", fixture_digest)
        manifest = {
            "name": MODEL_NAME,
            "version": registered.version,
            "variant": variant,
            "artifact_path": str(artifact),
            "artifact_sha256": artifact_digest,
            "dataset_digest": fixture_digest,
            "mlflow_run_id": run.info.run_id,
            "model_uri": info.model_uri,
            "delay_ms": delay_ms,
            "signature": {"inputs": "float[2]", "outputs": "int"},
            "created_by": "scripts/register_models.py",
        }
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest


def main() -> None:
    if MODELS.exists():
        shutil.rmtree(MODELS)
    MODELS.mkdir(parents=True)
    print("configuring MLflow", flush=True)
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("model-deployment-control-plane")
    client = MlflowClient()
    print("creating MLflow registered model", flush=True)
    try:
        client.create_registered_model(MODEL_NAME)
    except Exception as exc:  # model may already exist during a retry
        if "RESOURCE_ALREADY_EXISTS" not in str(exc) and "already exists" not in str(exc).lower():
            raise
    manifests = [
        register("champion", 0),
        register("candidate-good", 0),
        register("candidate-good-v2", 0),
        register("quality-bad", 0),
        register("slow", 700),
    ]
    client.set_registered_model_alias(MODEL_NAME, "champion", manifests[0]["version"])
    (MODELS / "registry.json").write_text(
        json.dumps({m["variant"]: m for m in manifests}, indent=2) + "\n"
    )
    print(json.dumps({"registered": manifests}, indent=2))


if __name__ == "__main__":
    main()
