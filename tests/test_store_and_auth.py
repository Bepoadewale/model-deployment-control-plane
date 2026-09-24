from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException
from modelcp.api import Store, canonical_hash, require_role


def test_sqlite_store_persists_release_approval_and_audit(tmp_path):
    path = tmp_path / "releases.db"
    first = Store(path)
    first.put_release({"id": "release-1", "state": "PROMOTION_PENDING"})
    first.add_approval("release-1", "approver-sam", "a" * 64)
    first.audit("RELEASE_APPROVED", "release-1", "approver-sam", plan_hash="a" * 64)
    first.close()

    recovered = Store(path)
    assert recovered.get_release("release-1")["state"] == "PROMOTION_PENDING"
    assert recovered.approval("release-1", "a" * 64)["approver"] == "approver-sam"
    assert recovered.audits("release-1")[0]["event_type"] == "RELEASE_APPROVED"
    recovered.close()


def test_plan_hash_is_deterministic_and_parameter_sensitive():
    base = {"candidate": "digest-1", "champion": "digest-0", "environment": "production"}
    assert canonical_hash(base) == canonical_hash(dict(reversed(list(base.items()))))
    assert canonical_hash(base) != canonical_hash({**base, "candidate": "digest-2"})


def test_invalid_or_unauthorized_jwt_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    verifier = require_role("approver")

    with pytest.raises(HTTPException, match="invalid token"):
        verifier(SimpleNamespace(headers={"authorization": "Bearer not-a-jwt"}))

    token = jwt.encode(
        {
            "sub": "developer",
            "tenant": "team-a",
            "roles": ["developer"],
            "principal_type": "human",
            "iss": "modelcp-local",
            "aud": "modelcp-api",
            "exp": int(time.time()) + 60,
        },
        "x" * 40,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException, match="not authorized"):
        verifier(SimpleNamespace(headers={"authorization": f"Bearer {token}"}))
