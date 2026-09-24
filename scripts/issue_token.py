#!/usr/bin/env python3
"""Emit local fixture identities for the demo; no production credential is involved."""

from __future__ import annotations

import argparse
import time

import jwt

parser = argparse.ArgumentParser()
parser.add_argument("subject")
parser.add_argument("--role", choices=["developer", "approver", "agent"], required=True)
args = parser.parse_args()
print(
    jwt.encode(
        {
            "sub": args.subject,
            "tenant": "team-a",
            "roles": [args.role],
            "principal_type": "agent" if args.role == "agent" else "human",
            "iss": "modelcp-local",
            "aud": "modelcp-api",
            "exp": int(time.time()) + 3600,
        },
        "local-release-secret-for-model-control-plane-2026",
        algorithm="HS256",
    )
)
