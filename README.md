# Wokelo OpenAPI Specification

Single-source-of-truth OpenAPI 3.0 specification for the Wokelo API suite.

The canonical spec is **`openapi.yaml`** at the repo root. A pre-bundled single-file version is published at **`dist/wokelo-openapi.yaml`** on every successful main-branch build.

## What's in here

| Path | Purpose |
|------|---------|
| `openapi.yaml` | Canonical merged spec — edit this |
| `sources/` | Original per-API YAMLs (12 files) kept for reference |
| `dist/wokelo-openapi.yaml` | Bundled spec — what directories should import |
| `dist/index.html` | Static Redoc HTML docs |
| `redocly.yaml` | Linter configuration |
| `.github/workflows/validate.yml` | CI validation + GitHub Pages deploy |

## Coverage

17 endpoints across 16 tags:

**Enrichment**
- Company Instant Enrichment — `POST /api/enterprise/company/enrich/` (instant mode)
- Company Deep Intelligence — `POST /api/enterprise/company/enrich/` (deep mode)
- Industry Deep Intelligence — `POST /api/enterprise/industry/enrich/`

**Discovery**
- Market Map — `POST /api/enterprise/market-map/enrich/`
- Target Screening — `POST /api/enterprise/target-screening/enrich/`
- Buyer Screening — `POST /api/enterprise/buyer-screening/enrich/`

**Monitoring**
- Company News Monitoring — `GET /api/enterprise/company/news/`

**Workflow**
- Company Research — `POST /api/company_primer/v3/start/` and workflow-manager variant
- Industry Research — `POST /api/industry_primer/v3/start/` and workflow-manager variant
- Peer Comparison — via workflow manager
- Custom Workflows — via workflow manager

**Supporting**
- Company Search, File Upload, Request Lifecycle (status / cancel / result), Report Lifecycle (status / download), Report Configuration

## Working on the spec

```bash
npm install
npm run lint        # validate spec
npm run preview     # live-reload doc preview at http://localhost:8080
npm run bundle      # produce dist/wokelo-openapi.yaml
npm run build-docs  # produce dist/index.html (static)
npm run build       # run all of the above
```

## Hosted URLs (once deployed)

- Canonical spec: `https://docs.wokelo.ai/openapi.yaml`
- Bundled spec: `https://raw.githubusercontent.com/wokelo-ai/openapi/main/dist/wokelo-openapi.yaml`
- Hosted docs: `https://wokelo-ai.github.io/openapi/`

## Directory submissions

When submitting to external API directories, use the **bundled** URL (resolves all refs into one file):

- APIs.guru / OpenAPI Directory — PR with bundled URL
- Postman API Network — import bundled URL
- SwaggerHub — import bundled URL
- OpenAPIHub, Apidog Hub — import bundled URL
- RapidAPI / APILayer / Zyla / ApyHub — import bundled URL + complete monetization onboarding
- Public APIs (GitHub) — one-line PR with docs link

## Two design decisions worth knowing

1. **Path collisions are merged with `oneOf`.** Two endpoints share a URL + method (`/api/enterprise/company/enrich/` and `/api/workflow_manager/start/`). Each is represented as a single operation whose request body is a `oneOf` of the supported modes. Every mode has a labeled example.

2. **Duplicate schemas are deduplicated.** When two source files defined schemas with the same name and identical content, one copy is kept. When the content differed, later copies are prefixed with a short tag (e.g. `CustomWFFundingRoundSummary`).

## Spec version

OpenAPI **3.0.3** — chosen over 3.1.0 for broader directory compatibility. All current features (oneOf, nullable, etc.) work identically.
