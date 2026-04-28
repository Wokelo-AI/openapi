#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
MASTER_PATH = ROOT / "openapi.yaml"
SOURCES_DIR = ROOT / "sources"
CODE_SAMPLES_PATH = ROOT / "scripts" / "code_samples.yaml"

OPERATIONS = {"get", "post", "put", "patch", "delete"}
LOGIN_OPERATION_ID = "post_auth_token"

UNAUTHORIZED_SCHEMA_NAME = "CommonUnauthorizedError"
UNAUTHORIZED_RESPONSE_NAME = "UnauthorizedError"
UNAUTHORIZED_RESPONSE_REF = f"#/components/responses/{UNAUTHORIZED_RESPONSE_NAME}"
UNAUTHORIZED_SCHEMA_REF = f"#/components/schemas/{UNAUTHORIZED_SCHEMA_NAME}"
BEARER_AUTH_DESCRIPTION = (
    "Use `Authorization: Bearer <JWT>` for authenticated requests. "
    "Obtain the token from `POST /auth/token/` and pass it in the request header."
)

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

REQUEST_EXAMPLES_BY_OPERATION_ID = {
    "post_auth_token": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "username": "sam@abconsulting.com",
        "password": "password",
        "grant_type": "password",
    },
    "post_api_assets_download_report": {
        "report_id": 84102,
        "file_type": "json",
    },
    "post_api_assets_upload": {
        "files": ["<binary file>"],
        "fileUUID": ["550e8400-e29b-41d4-a716-446655440000"],
    },
    "post_api_enterprise_buyer-screening_enrich": {
        "company": "acme-security",
        "parameters": {
            "buyer_type": ["strategic"],
            "company_type": "public",
            "geography": ["USA"],
        },
    },
    "post_api_enterprise_industry_enrich": {
        "topic": "Enterprise SaaS security",
        "sections": [
            "market_size",
            "trends_and_innovations",
            "transactions_mna",
        ],
        "parameters": {
            "keywords": ["zero trust", "SIEM"],
            "geography": ["USA"],
            "definition": "B2B software focused on enterprise cybersecurity",
            "sample_companies": ["crowdstrike", "sentinel"],
        },
    },
    "post_api_enterprise_market-map_enrich": {
        "topic": "AI-powered CRM software",
        "parameters": {
            "detailed_query": "B2B CRM tools leveraging AI for sales automation",
            "keywords": ["AI", "CRM", "sales automation"],
            "sample_companies": ["salesforce", "hubspot"],
            "geography": ["USA"],
            "company_type": "private",
            "employee_count": ["11-50"],
            "funding_stage": ["Series A", "Series B"],
        },
    },
    "post_api_enterprise_request_cancel": {
        "request_id": "5b0eff600-366f-465c-b795-68837043a2d3",
    },
    "post_api_enterprise_target-screening_enrich": {
        "company": "microsoft",
        "parameters": {
            "detailed_query": "Looking for B2B SaaS companies in the cybersecurity space",
            "keywords": ["zero trust", "endpoint security"],
            "geography": ["USA"],
            "company_type": "private",
        },
    },
    "post_api_news_fetch": {
        "report_id": 72053,
        "page": 1,
        "page_size": 500,
    },
    "post_api_news_start": {
        "website": "wokelo.ai",
        "permalink": "wokelo",
    },
    "post_api_wkl_notebook_configuration": {
        "notebook_id": 103737,
    },
}

SKIP_MASTER_MULTI_EXAMPLE_KEYS = {
    ("post", "/api/enterprise/company/enrich/"),
}
SKIP_MASTER_MULTI_EXAMPLE_OPERATION_IDS = {
    "post_api_enterprise_company_enrich",
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


def load_code_samples_data() -> dict:
    if not CODE_SAMPLES_PATH.exists():
        return {}
    return yaml.safe_load(CODE_SAMPLES_PATH.read_text()) or {}


def ensure_common_unauthorized(spec: dict) -> None:
    components = ensure_components(spec)
    security_schemes = components.setdefault("securitySchemes", {})
    bearer_auth = security_schemes.setdefault(
        "bearerAuth",
        {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    )
    bearer_auth["description"] = BEARER_AUTH_DESCRIPTION

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


def slugify_example_name(value: str) -> str:
    slug = []
    previous_underscore = False
    for char in value.lower():
        if char.isalnum():
            slug.append(char)
            previous_underscore = False
        elif not previous_underscore:
            slug.append("_")
            previous_underscore = True
    return "".join(slug).strip("_") or "example"


def get_schema_example(schema: dict, spec: dict) -> dict | list | str | int | float | bool | None:
    if not isinstance(schema, dict):
        return None
    if "example" in schema:
        return schema["example"]
    ref = schema.get("$ref")
    if not ref or not ref.startswith("#/components/schemas/"):
        return None
    schema_name = ref.rsplit("/", 1)[-1]
    component_schema = spec.get("components", {}).get("schemas", {}).get(schema_name, {})
    return component_schema.get("example")


def set_request_body_examples(op: dict, spec: dict) -> None:
    request_body = op.get("requestBody")
    if not request_body:
        return

    manual_example = REQUEST_EXAMPLES_BY_OPERATION_ID.get(op.get("operationId"))
    for media in request_body.get("content", {}).values():
        if manual_example is not None:
            media.pop("examples", None)
            media["example"] = manual_example
            continue
        schema_example = get_schema_example(media.get("schema", {}), spec)
        if "examples" in media or "example" in media:
            continue
        if schema_example is not None:
            media["example"] = schema_example


def set_code_samples(op: dict, samples: list[dict]) -> None:
    if samples:
        op["x-codeSamples"] = deepcopy(samples)
    else:
        op.pop("x-codeSamples", None)


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

    set_request_body_examples(op, {})


def build_source_description_map() -> dict[tuple[str, str], list[str]]:
    mapping: dict[tuple[str, str], list[str]] = {}
    for path in sorted(SOURCES_DIR.glob("*.yaml")):
        spec = load_yaml(path)
        for op_path, method, _op in iter_operations(spec):
            mapping.setdefault((method, op_path), []).append(spec["info"]["description"].strip())
    return mapping


def build_source_request_examples_map() -> dict[tuple[str, str], list[tuple[str, dict]]]:
    mapping: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    for path in sorted(SOURCES_DIR.glob("*.yaml")):
        spec = load_yaml(path)
        title = spec.get("info", {}).get("title", path.stem)
        for op_path, method, op in iter_operations(spec):
            request_body = op.get("requestBody", {})
            for media in request_body.get("content", {}).values():
                if "examples" in media:
                    for example_name, example_value in media["examples"].items():
                        value = example_value.get("value")
                        if value is not None:
                            mapping.setdefault((method, op_path), []).append((example_name, value))
                elif "example" in media:
                    mapping.setdefault((method, op_path), []).append((slugify_example_name(title), media["example"]))
    return mapping


def build_source_code_samples_map(code_samples_data: dict) -> dict[tuple[str, str], list[dict]]:
    mapping: dict[tuple[str, str], list[dict]] = {}
    for entry in code_samples_data.values():
        key = (entry["method"], entry["path"])
        mapping.setdefault(key, []).append(entry)
    return mapping


def build_master_code_samples(entries: list[dict]) -> list[dict]:
    if not entries:
        return []
    if len(entries) == 1:
        return deepcopy(entries[0].get("samples", []))

    merged: list[dict] = []
    for entry in entries:
        variant_title = entry["title"]
        filtered_samples = [
            sample for sample in entry.get("samples", [])
            if sample.get("lang") in {"cURL", "Python"}
        ]
        if not filtered_samples:
            filtered_samples = entry.get("samples", [])[:1]
        for sample in filtered_samples:
            merged.append({
                "lang": sample["lang"],
                "label": f"{variant_title} · {sample.get('label', sample['lang'])}",
                "source": sample["source"],
            })
    return merged


def polish_source(path: Path) -> None:
    spec = load_yaml(path)
    ensure_common_unauthorized(spec)
    code_samples_data = load_code_samples_data()

    info_description = spec["info"]["description"].strip()
    for op_path, method, op in iter_operations(spec):
        cleanup_operation(
            op,
            info_description,
            add_401=op.get("operationId") != LOGIN_OPERATION_ID,
            normalize_cancel=op.get("operationId") == "post_api_enterprise_request_cancel",
            normalize_notebook=op.get("operationId") == "post_api_wkl_notebook_configuration",
        )
        set_request_body_examples(op, spec)
        set_code_samples(op, code_samples_data.get(op.get("operationId"), {}).get("samples", []))

    dump_yaml(path, spec)


def polish_master() -> None:
    spec = load_yaml(MASTER_PATH)
    ensure_common_unauthorized(spec)

    description_map = build_source_description_map()
    source_request_examples = build_source_request_examples_map()
    code_samples_data = load_code_samples_data()
    source_code_samples = build_source_code_samples_map(code_samples_data)

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
        set_request_body_examples(op, spec)
        set_code_samples(op, build_master_code_samples(source_code_samples.get(key, [])))

        key = (method, op_path)
        request_body = op.get("requestBody")
        if not request_body:
            continue
        for media in request_body.get("content", {}).values():
            examples = source_request_examples.get(key, [])
            if key in SKIP_MASTER_MULTI_EXAMPLE_KEYS or op.get("operationId") in SKIP_MASTER_MULTI_EXAMPLE_OPERATION_IDS:
                media.pop("example", None)
                media.pop("examples", None)
                continue
            if "examples" in media:
                continue
            if len(examples) > 1:
                media.pop("example", None)
                media["examples"] = {
                    name: {"value": value}
                    for name, value in examples
                }
            elif len(examples) == 1 and "example" not in media:
                media["example"] = examples[0][1]

    dump_yaml(MASTER_PATH, spec)


def main() -> None:
    for source_file in sorted(SOURCES_DIR.glob("*.yaml")):
        polish_source(source_file)
    polish_master()


if __name__ == "__main__":
    main()
