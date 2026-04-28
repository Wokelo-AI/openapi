#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
MASTER_PATH = ROOT / "openapi.yaml"
SOURCES_DIR = ROOT / "sources"

OPERATIONS = {"get", "post", "put", "patch", "delete"}
LOGIN_OPERATION_ID = "post_auth_token"

UNAUTHORIZED_SCHEMA_NAME = "CommonUnauthorizedError"
UNAUTHORIZED_RESPONSE_NAME = "UnauthorizedError"
UNAUTHORIZED_RESPONSE_REF = f"#/components/responses/{UNAUTHORIZED_RESPONSE_NAME}"
UNAUTHORIZED_SCHEMA_REF = f"#/components/schemas/{UNAUTHORIZED_SCHEMA_NAME}"

MERGED_DESCRIPTIONS = {
    ("post", "/api/workflow_manager/start/"): (
        "Start a workflow-driven report through Wokelo's workflow manager. "
        "This shared endpoint supports Company Research (`company_primer`), "
        "Industry Research (`industry_primer`), Peer Comparison (`player_comparison`), "
        "and Custom Workflows (dashboard-configured workflow IDs). "
        "The request body is modeled as a discriminator-based union across those variants."
    ),
    ("post", "/api/enterprise/company/enrich/"): (
        "Enrich one or more companies through Wokelo's shared company enrichment endpoint. "
        "This operation supports the Company Instant Enrichment and Company Deep Intelligence "
        "request variants using a discriminator-based request body."
    ),
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def dump_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000)
    )


def iter_operations(spec: dict):
    for path, item in spec.get("paths", {}).items():
        for method, op in item.items():
            if method in OPERATIONS:
                yield path, method, op


def ensure_components(spec: dict) -> dict:
    return spec.setdefault("components", {})


def ensure_common_unauthorized(spec: dict) -> None:
    components = ensure_components(spec)
    schemas = components.setdefault("schemas", {})
    responses = components.setdefault("responses", {})
    schemas[UNAUTHORIZED_SCHEMA_NAME] = {
        "type": "object",
        "description": (
            "Generic authentication error returned when the request is missing a valid bearer token."
        ),
        "properties": {
            "detail": {"type": "string"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
        "additionalProperties": True,
        "example": {"detail": "Authentication credentials were not provided."},
    }
    responses[UNAUTHORIZED_RESPONSE_NAME] = {
        "description": "Unauthorized. Include a valid bearer token from `/auth/token/`.",
        "content": {
            "application/json": {
                "schema": {"$ref": UNAUTHORIZED_SCHEMA_REF},
                "example": {"detail": "Authentication credentials were not provided."},
            }
        },
    }


def normalize_request_cancel(op: dict) -> None:
    params = op.get("parameters", [])
    filtered = [
        p for p in params if not (p.get("in") == "query" and p.get("name") == "request_id")
    ]
    if filtered:
        op["parameters"] = filtered
    elif "parameters" in op:
        del op["parameters"]

    responses = op.setdefault("responses", {})
    if "200" in responses and "content" not in responses["200"]:
        responses["200"]["description"] = "Successful cancellation acknowledgement"
        responses["200"]["content"] = {
            "application/json": {
                "schema": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": (
                        "Cancellation acknowledgement payload. The exact success body "
                        "is not formally documented."
                    ),
                }
            }
        }


def normalize_notebook_configuration(op: dict) -> None:
    responses = op.setdefault("responses", {})
    if "200" in responses and "content" not in responses["200"]:
        responses["200"]["description"] = "Notebook configuration returned successfully"
        responses["200"]["content"] = {
            "application/json": {
                "schema": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": (
                        "Notebook configuration object. The docs describe this as "
                        "the original workflow configuration and do not formalize the shape."
                    ),
                }
            }
        }


def cleanup_operation(
    op: dict,
    description: str,
    *,
    add_401: bool,
    normalize_cancel: bool,
    normalize_notebook: bool,
) -> None:
    op["description"] = description.strip()
    op.pop("x-source-variants", None)

    responses = op.setdefault("responses", {})
    if add_401 and "401" not in responses:
        responses["401"] = {"$ref": UNAUTHORIZED_RESPONSE_REF}

    if "400" in responses and responses["400"].get("description") == "Company primer":
        responses["400"]["description"] = "Bad request"

    if normalize_cancel:
        normalize_request_cancel(op)
    if normalize_notebook:
        normalize_notebook_configuration(op)


def build_source_description_map() -> dict[tuple[str, str], list[str]]:
    mapping: dict[tuple[str, str], list[str]] = {}
    for path in sorted(SOURCES_DIR.glob("*.yaml")):
        spec = load_yaml(path)
        for op_path, method, _op in iter_operations(spec):
            mapping.setdefault((method, op_path), []).append(spec["info"]["description"].strip())
    return mapping


def polish_source(path: Path) -> None:
    spec = load_yaml(path)
    ensure_common_unauthorized(spec)

    info_description = spec["info"]["description"].strip()
    for op_path, method, op in iter_operations(spec):
        cleanup_operation(
            op,
            info_description,
            add_401=op.get("operationId") != LOGIN_OPERATION_ID,
            normalize_cancel=op.get("operationId") == "post_api_enterprise_request_cancel",
            normalize_notebook=op.get("operationId") == "post_api_wkl_notebook_configuration",
        )

    dump_yaml(path, spec)


def polish_master() -> None:
    spec = load_yaml(MASTER_PATH)
    ensure_common_unauthorized(spec)

    description_map = build_source_description_map()
    description_counter = Counter(description_map)

    for op_path, method, op in iter_operations(spec):
        key = (method, op_path)
        if key in MERGED_DESCRIPTIONS:
            description = MERGED_DESCRIPTIONS[key]
        else:
            descriptions = description_map.get(key, [])
            description = descriptions[0] if descriptions else op.get("description", "")

        cleanup_operation(
            op,
            description,
            add_401=op.get("operationId") != LOGIN_OPERATION_ID,
            normalize_cancel=op.get("operationId") == "post_api_enterprise_request_cancel",
            normalize_notebook=op.get("operationId") == "post_api_wkl_notebook_configuration",
        )

    dump_yaml(MASTER_PATH, spec)


def main() -> None:
    for source_file in sorted(SOURCES_DIR.glob("*.yaml")):
        polish_source(source_file)
    polish_master()


if __name__ == "__main__":
    main()
