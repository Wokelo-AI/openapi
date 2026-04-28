# Wokelo OpenAPI Specification

Single-source-of-truth OpenAPI 3.0.3 specification for the Wokelo API suite.

The canonical spec is **`openapi.yaml`** at the repo root. A pre-bundled single-file version is published at **`dist/wokelo-openapi.yaml`** on every successful `main` branch build.

## What's in here

| Path | Purpose |
|------|---------|
| `openapi.yaml` | Canonical merged spec for the full Wokelo API |
| `sources/` | 26 standalone capability specs, one per official docs page |
| `dist/wokelo-openapi.yaml` | Bundled spec for import into external tools and directories |
| `dist/index.html` | Public Redoc reference docs (client-rendered to avoid hydration issues) |
| `dist/swagger.html` | Interactive Swagger UI playground backed by the bundled spec |
| `redocly.yaml` | Linter configuration |
| `.github/workflows/validate.yml` | CI validation + GitHub Pages deploy |
| `scripts/polish_specs.py` | Normalizes public-facing descriptions, auth error coverage, and known docs inconsistencies across the master and sources |

## Coverage

Version `2.0.0` covers:

- 22 unique OpenAPI operations in the canonical master spec
- 26 standalone capability specs under `sources/`
- 6 top-level tags in the merged spec

The 26 capability files map to the official Wokelo docs set:

- Authentication: Login
- Enrichment: Company Instant Enrichment, Company Deep Intelligence, Industry Deep Intelligence, Fetch Filings Data, Employee Reviews, Fetch Earnings Transcripts, Product Reviews
- Discovery: Market Map, Target Screening, Buyer Screening, Company Search
- Monitoring: Company News Monitoring, Legacy Initiate News Report, Legacy Fetch News Report
- Workflow Automation: Company Research, Industry Research, Peer Comparison, Custom Workflows
- Supporting APIs: Upload File, Request Status, Request Cancel, Request Result, Get Report Status, Download Report, Notebook Configuration

## Working on the spec

```bash
npm install
npm run polish-specs # normalize master + standalone files after spec refreshes
npm run lint        # validate openapi.yaml
npm run preview     # live-reload doc preview at http://localhost:8080
npm run bundle      # produce dist/wokelo-openapi.yaml
npm run build-docs  # produce dist/index.html from the Redoc template
npm run build-docs-ssr # optional: generate Redocly's prerendered HTML for comparison/debugging
npm run build-playground # produce dist/swagger.html
npm run build       # lint + bundle + docs
```

## Hosted URLs (once deployed)

- Canonical spec: `https://docs.wokelo.ai/openapi.yaml`
- Bundled spec: `https://raw.githubusercontent.com/Wokelo-AI/openapi/main/dist/wokelo-openapi.yaml`
- Hosted docs: `https://wokelo-ai.github.io/openapi/`
- Interactive playground: `https://wokelo-ai.github.io/openapi/swagger.html`

## Directory submissions

When submitting to external API directories, use the **bundled** URL so every `$ref` is resolved into one file:

- APIs.guru / OpenAPI Directory
- Postman API Network
- SwaggerHub
- OpenAPIHub / Apidog Hub
- RapidAPI / APILayer / Zyla / ApyHub
- Public APIs (GitHub)

## Design notes

1. **Two shared server paths are merged in the master spec.** OpenAPI allows only one operation per method + path, so `POST /api/workflow_manager/start/` and `POST /api/enterprise/company/enrich/` are represented once each in `openapi.yaml` using `oneOf` plus discriminators. The standalone files in `sources/` keep those same real paths but narrow the request body to a single documented capability.

2. **The master spec is docs-authoritative.** This repo now follows the current official Wokelo docs and Postman collection. As part of the `2.0.0` refresh, the older direct primer endpoints (`/api/company_primer/v3/start/` and `/api/industry_primer/v3/start/`) were removed from the canonical spec because they are not part of the current official capability set.

3. **Redoc and interactive testing are split intentionally.** The published `dist/index.html` uses Redoc CE for the reference experience, while `dist/swagger.html` provides Swagger UI-based request execution against the same bundled OpenAPI file. Redocly's full hosted/API-docs products support a Try It console, but plain Redoc CE does not.

4. **The published Redoc page is client-rendered on purpose.** Redocly CLI's prerendered `build-docs` output currently produces browser-side hydration errors for this large spec even though the spec is valid. To keep the public docs clean, this repo publishes a client-rendered Redoc template at `dist/index.html` and keeps `npm run build-docs-ssr` only as an optional debugging path.

## Normalized doc inconsistencies

These are current inconsistencies in the upstream markdown docs or Postman material that the published OpenAPI intentionally normalizes:

- `POST /api/enterprise/request/cancel`
  The markdown page declares `request_id` as a query parameter, but the official code samples and Postman collection send it in the JSON body. The spec models it as a request-body field.
- `POST /api/assets/upload/`
  The markdown header parameter table says `Content-Type: application/json`, but the executable examples and Postman collection use `multipart/form-data`. The spec models the real multipart upload contract.
- `POST /api/wkl/notebook/configuration/`
  The markdown endpoint line omits the leading slash, but the code samples and Postman collection include the canonical `/api/...` path. The spec keeps the canonical path.
- `POST /api/workflow_manager/start/` for Peer Comparison
  The peer-comparison markdown endpoint omits the trailing slash while sibling workflow docs and Postman use `/api/workflow_manager/start/`. The spec keeps the trailing slash to match the live server path used elsewhere.

## Versioning

- OpenAPI version: `3.0.3`
- Spec release version: `2.0.0`

`2.0.0` is a semver-major refresh because the published canonical spec changed its endpoint set and now tracks the current official docs corpus directly.
