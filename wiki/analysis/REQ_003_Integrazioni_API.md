---
title: "Integrazioni API - REQ-003"
type: integration
tags: [integration, api]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_003_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-003"
status: validated
authority: validated_report
---
# Integrazioni API - REQ-003

Il client API ora copre:
- Salesforce SOQL via REST, gia' presente.
- Data Cloud Query API: submit, status, rows e cancel.
- Data Cloud Metadata API: lookup filtrabile per entity type, category e name.
- Data Cloud Ingestion API: streaming validation, streaming ingest, bulk create job, upload CSV, close job e status.

Nuove variabili ambiente:
- `SALESFORCE_DATACLOUD_API_URL`
- `SALESFORCE_DATACLOUD_INGESTION_URL`
- `SALESFORCE_JOURNAL_REDACT_FIELDS`

Variabili esistenti mantenute:
- `SALESFORCE_DATACLOUD_QUERY_URL`
- `SALESFORCE_DATACLOUD_ACCESS_TOKEN`

Gli endpoint Data Cloud restano configurabili per tenant e setup org-specific.
