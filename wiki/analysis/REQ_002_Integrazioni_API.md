---
title: "Integrazioni API - REQ-002"
type: integration
tags: [integration, api]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_002_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-002"
status: validated
authority: validated_report
---
# Integrazioni API - REQ-002

E' stato aggiunto `SalesforceApiClient` basato su librerie standard Python.

Configurazione Salesforce standard:
- `SALESFORCE_INSTANCE_URL`
- `SALESFORCE_ACCESS_TOKEN`
- `SALESFORCE_API_VERSION`

Configurazione Data Cloud:
- `SALESFORCE_DATACLOUD_QUERY_URL`
- `SALESFORCE_DATACLOUD_ACCESS_TOKEN`

L'endpoint Data Cloud e' intenzionalmente configurabile per evitare assunzioni non verificate su URL e setup specifici dell'org.