#!/usr/bin/env python3
"""Validate the cross-file invariants of an Adversarial Claim Graph.

Uses Python's standard library only. JSON Schema files are included as
documentation and interoperability aids; this script checks the graph's
cross-file semantic invariants.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

NODE_STATUSES = {
    "PENDING", "RUNNING", "PASS", "REPAIR_REQUIRED",
    "UNRESOLVED", "BLOCKED", "INVALIDATED"
}
CLAIM_STATUSES = {
    "PROPOSED", "SUPPORTED", "CHALLENGED", "REPAIRED",
    "ACCEPTED", "REJECTED", "UNRESOLVED"
}
VERDICTS = {"ACCEPT", "REJECT", "UNRESOLVED"}

FILES = {
    "graph": "graph-state.json",
    "claims": "claim-ledger.json",
    "challenges": "challenge-ledger.json",
    "supports": "support-ledger.json",
    "arbiter": "arbiter-ledger.json",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if type(value) is not dict:
        raise ValidationError(f"{path} must contain one JSON object")
    return value


def require_list(obj: dict[str, Any], key: str) -> list[Any]:
    value = obj.get(key)
    if type(value) is not list:
        raise ValidationError(f"{key} must be a list")
    return value


def unique_rows(rows: list[Any], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValidationError(f"{label}[{index}] must be an object")
        ident = row.get(key)
        if type(ident) is not str or not ident:
            raise ValidationError(f"{label}[{index}].{key} must be a non-empty string")
        if ident in result:
            raise ValidationError(f"duplicate {label} ID: {ident}")
        result[ident] = row
    return result


def validate(directory: Path) -> dict[str, Any]:
    data = {name: load_json(directory / filename) for name, filename in FILES.items()}

    graph_id = data["graph"].get("graph_id")
    if type(graph_id) is not str or not graph_id:
        raise ValidationError("graph-state.json graph_id must be a non-empty string")
    for name, obj in data.items():
        if obj.get("graph_id") != graph_id:
            raise ValidationError(f"{FILES[name]} graph_id does not match {graph_id}")

    nodes = unique_rows(require_list(data["graph"], "nodes"), "node_id", "nodes")
    running = []
    for node_id, node in nodes.items():
        status = node.get("status")
        if status not in NODE_STATUSES:
            raise ValidationError(f"node {node_id} has invalid status {status!r}")
        if status == "RUNNING":
            running.append(node_id)
        deps = node.get("depends_on")
        if type(deps) is not list or any(type(x) is not str for x in deps):
            raise ValidationError(f"node {node_id} depends_on must be a string list")
        unknown = sorted(set(deps) - set(nodes))
        if unknown:
            raise ValidationError(f"node {node_id} has unknown dependencies: {unknown}")
        if node_id in deps:
            raise ValidationError(f"node {node_id} depends on itself")
        if status == "PASS":
            receipt = node.get("receipt_path")
            if type(receipt) is not str or not receipt:
                raise ValidationError(f"PASS node {node_id} lacks receipt_path")
    if len(running) > 1:
        raise ValidationError(f"more than one RUNNING node: {running}")

    frontier = data["graph"].get("active_frontier")
    if type(frontier) is not list or any(type(x) is not str for x in frontier):
        raise ValidationError("active_frontier must be a string list")
    unknown_frontier = sorted(set(frontier) - set(nodes))
    if unknown_frontier:
        raise ValidationError(f"active_frontier has unknown nodes: {unknown_frontier}")

    claims = unique_rows(require_list(data["claims"], "claims"), "claim_id", "claims")
    for claim_id, claim in claims.items():
        status = claim.get("status")
        if status not in CLAIM_STATUSES:
            raise ValidationError(f"claim {claim_id} has invalid status {status!r}")
        node = claim.get("introduced_by_node")
        if node not in nodes:
            raise ValidationError(f"claim {claim_id} introduced by unknown node {node!r}")
        deps = claim.get("depends_on", [])
        if type(deps) is not list or any(type(x) is not str for x in deps):
            raise ValidationError(f"claim {claim_id} depends_on must be a string list")
        unknown = sorted(set(deps) - set(claims))
        if unknown:
            raise ValidationError(f"claim {claim_id} has unknown dependencies: {unknown}")
        invalidates = claim.get("invalidates_nodes", [])
        if type(invalidates) is not list or any(type(x) is not str for x in invalidates):
            raise ValidationError(f"claim {claim_id} invalidates_nodes must be a string list")
        unknown_nodes = sorted(set(invalidates) - set(nodes))
        if unknown_nodes:
            raise ValidationError(f"claim {claim_id} invalidates unknown nodes: {unknown_nodes}")

    challenges = unique_rows(
        require_list(data["challenges"], "challenges"), "challenge_id", "challenges"
    )
    for challenge_id, challenge in challenges.items():
        if challenge.get("claim_id") not in claims:
            raise ValidationError(
                f"challenge {challenge_id} references unknown claim {challenge.get('claim_id')!r}"
            )

    supports = unique_rows(
        require_list(data["supports"], "supports"), "support_id", "supports"
    )
    for support_id, support in supports.items():
        if support.get("challenge_id") not in challenges:
            raise ValidationError(
                f"support {support_id} references unknown challenge {support.get('challenge_id')!r}"
            )

    verdict_rows = unique_rows(
        require_list(data["arbiter"], "claim_verdicts"), "claim_id", "claim_verdicts"
    )
    for claim_id, row in verdict_rows.items():
        if claim_id not in claims:
            raise ValidationError(f"arbiter verdict references unknown claim {claim_id}")
        if row.get("verdict") not in VERDICTS:
            raise ValidationError(f"claim {claim_id} has invalid arbiter verdict")

    readiness = data["graph"].get("readiness")
    if type(readiness) is not bool:
        raise ValidationError("graph readiness must be boolean")

    critical = {
        claim_id: claim
        for claim_id, claim in claims.items()
        if claim.get("readiness_critical") is True
    }
    missing_verdicts = sorted(set(critical) - set(verdict_rows))
    nonaccepted = sorted(
        claim_id
        for claim_id in critical
        if verdict_rows.get(claim_id, {}).get("verdict") != "ACCEPT"
    )

    global_verdict = data["arbiter"].get("global_verdict")
    if global_verdict not in VERDICTS:
        raise ValidationError("arbiter global_verdict must be ACCEPT, REJECT, or UNRESOLVED")

    if readiness:
        if missing_verdicts:
            raise ValidationError(
                f"readiness=true but critical claims lack verdicts: {missing_verdicts}"
            )
        if nonaccepted:
            raise ValidationError(
                f"readiness=true but critical claims are not accepted: {nonaccepted}"
            )
        if global_verdict != "ACCEPT":
            raise ValidationError(
                f"readiness=true but global arbiter verdict is {global_verdict}"
            )

    if global_verdict == "ACCEPT" and nonaccepted:
        raise ValidationError(
            f"global ACCEPT conflicts with nonaccepted critical claims: {nonaccepted}"
        )

    return {
        "result": "PASS",
        "graph_id": graph_id,
        "node_count": len(nodes),
        "running_nodes": running,
        "active_frontier": frontier,
        "claim_count": len(claims),
        "readiness_critical_claims": len(critical),
        "challenge_count": len(challenges),
        "support_count": len(supports),
        "arbiter_verdict_count": len(verdict_rows),
        "global_verdict": global_verdict,
        "readiness": readiness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.directory)
    except ValidationError as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
