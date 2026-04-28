# Directory Submission Guide

Concrete steps for submitting the Wokelo OpenAPI spec to each directory. Assumes `dist/wokelo-openapi.yaml` is hosted at a public URL.

## Prerequisites

Host the bundled spec at a stable public URL. Recommended:
- Primary: `https://docs.wokelo.ai/openapi.yaml`
- Mirror: `https://raw.githubusercontent.com/wokelo-ai/openapi/main/dist/wokelo-openapi.yaml`

Ensure the URL:
- Returns `Content-Type: application/yaml` (or `text/yaml`)
- Has CORS header `Access-Control-Allow-Origin: *` so browser tools can fetch
- Is versioned (tag git releases `v2.0.0`, `v2.1.0` etc.)

---

## Tier 1 — Free, fast, high-signal (do all of these)

### 1. APIs.guru (OpenAPI Directory)
- **Time:** 20 min
- **Steps:**
  1. Fork `https://github.com/APIs-guru/openapi-directory`
  2. Add your spec under `APIs/wokelo.ai/2.0.0/openapi.yaml` (or submit URL in registry)
  3. Open PR with title "Add Wokelo API"
  4. Maintainers auto-validate and merge
- **Result:** Listed on `https://apis.guru/` and `https://api.apis.guru/v2/list.json` — used by many downstream tools

### 2. Public APIs (GitHub)
- **Time:** 10 min
- **Steps:**
  1. Fork `https://github.com/public-apis/public-apis`
  2. Add entry under relevant category (likely "Business" or "Finance")
  3. One line: `| Wokelo | Deal intelligence API | apiKey | Yes | Yes | [Link](https://docs.wokelo.ai) |`
  4. Open PR
- **Result:** Listed in the most-starred API README on GitHub

### 3. Postman API Network
- **Time:** 20 min
- **Steps:**
  1. Sign up / log in at postman.com
  2. Create team workspace "Wokelo"
  3. In APIs tab → "Import" → paste spec URL or upload file
  4. Auto-generates collection + docs
  5. Publish workspace to Public API Network (settings → visibility → public)
- **Result:** Searchable in Postman app + web network

### 4. SwaggerHub
- **Time:** 15 min
- **Steps:**
  1. Sign up free at swaggerhub.com
  2. Create API → "Import" → paste URL
  3. Set visibility to Public
  4. Optionally enable auto-sync from GitHub
- **Result:** Hosted docs + mocks + codegen at swaggerhub.com/apis/wokelo/api

### 5. OpenAPIHub
- **Time:** 15 min
- **Steps:**
  1. Sign up at openapihub.com
  2. Submit API → import OpenAPI spec URL
  3. Fill out category, logo, description
- **Result:** Listed in directory, contributes to OpenAPI ecosystem visibility

### 6. Apidog Hub
- **Time:** 15 min
- **Steps:**
  1. Sign up at apidog.com
  2. Create workspace → import OpenAPI spec URL
  3. Publish as public API
- **Result:** Listed in Apidog's marketplace, accessible to their dev community

---

## Tier 2 — Monetized marketplaces (do if you want self-serve dev traffic)

These require pricing tiers, endpoint testing, and provider verification. Approval takes 3–10 business days.

### 7. RapidAPI
- **Time:** 2–4 hours onboarding + 3–5 days approval
- **Process:**
  1. Sign up as API provider at rapidapi.com/provider
  2. Add New API → "Import OpenAPI" → paste URL
  3. Configure base URL, headers (Authorization), transformations if needed
  4. Set pricing tiers (free tier + paid)
  5. Add endpoint test requests for each operation
  6. Configure payout info
  7. Submit for review
- **Pros:** Large indie-dev audience, built-in billing
- **Cons:** 20% revenue share, audience skews toward low-value indie projects

### 8. APILayer
- **Time:** Similar to RapidAPI
- **Process:** Contact sales → onboarding via account manager → OpenAPI import → pricing setup

### 9. Zyla API Hub
- **Time:** Similar
- **Process:** Provider signup at zylalabs.com → import OpenAPI → pricing → review

### 10. ApyHub
- **Time:** Similar
- **Process:** Provider signup at apyhub.com → import → pricing → review

---

## Skip

### Apify Store
Designed for Apify Actors (scraping bots), not REST APIs. Listing would require wrapping each endpoint in an Actor — a separate engineering project with limited ROI.

---

## Tracking template

| Directory | Submitted | Approved | Live URL |
|-----------|-----------|----------|----------|
| APIs.guru | [ ] | [ ] | |
| Public APIs | [ ] | [ ] | |
| Postman Network | [ ] | [ ] | |
| SwaggerHub | [ ] | [ ] | |
| OpenAPIHub | [ ] | [ ] | |
| Apidog Hub | [ ] | [ ] | |
| RapidAPI | [ ] | [ ] | |
| APILayer | [ ] | [ ] | |
| Zyla API Hub | [ ] | [ ] | |
| ApyHub | [ ] | [ ] | |

## After submission

- Add directory badges to your website and docs
- Monitor incoming traffic from each source (UTM tags help)
- When you publish v2.1, most directories auto-refetch from your hosted URL; Postman/SwaggerHub may need manual re-import
