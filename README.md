# Wokelo OpenAPI Specification

Single-source-of-truth OpenAPI 3.0.3 specification for the Wokelo API suite.

The canonical spec is **`openapi.yaml`** at the repo root. A pre-bundled single-file version is published at **`dist/wokelo-openapi.yaml`** on every successful `main` branch build.

## What's in here

| Path | Purpose |
|------|---------|
| `openapi.yaml` | Canonical merged spec for the full Wokelo API |
| `sources/` | 26 standalone capability specs, one per official docs page |
| `dist/wokelo-openapi.yaml` | Bundled spec for import into external tools and directories |
| `dist/index.html` | Static Redoc HTML docs |
| `redocly.yaml` | Linter configuration |
| `.github/workflows/validate.yml` | CI validation + GitHub Pages deploy |

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
npm run lint        # validate openapi.yaml
npm run preview     # live-reload doc preview at http://localhost:8080
npm run bundle      # produce dist/wokelo-openapi.yaml
npm run build-docs  # produce dist/index.html
npm run build       # lint + bundle + docs
```

## Hosted URLs (once deployed)

- Canonical spec: `https://docs.wokelo.ai/openapi.yaml`
- Bundled spec: `https://raw.githubusercontent.com/Wokelo-AI/openapi/main/dist/wokelo-openapi.yaml`
- Hosted docs: `https://wokelo-ai.github.io/openapi/`

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

## Versioning

- OpenAPI version: `3.0.3`
- Spec release version: `2.0.0`

`2.0.0` is a semver-major refresh because the published canonical spec changed its endpoint set and now tracks the current official docs corpus directly.
