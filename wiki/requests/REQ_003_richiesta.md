---
title: "Richiesta REQ-003"
type: request
tags: [request, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_003_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-003"
status: validated
authority: validated_report
---
# Richiesta REQ-003

## Contesto
Obiettivo: Estensione Data Cloud MCP con Query API, Metadata API, ingestion supervisionata, workflow registry e validazioni avanzate.

File o fonti collegate:
- salesforce_mcp/api_client.py
- salesforce_mcp/workflows.py
- salesforce_mcp/execution.py
- salesforce_mcp/server.py
- salesforce_mcp/config.py
- salesforce_mcp/journal.py
- tests/test_api_client.py
- tests/test_execution.py
- README.md
- mcp.example.json
- docs/changelogs/2026-06-21_datacloud_api_registry.md

## Modifiche funzionali
Sono stati aggiunti tool MCP Data Cloud strutturati:
- `datacloud_submit_query`
- `datacloud_query_status`
- `datacloud_query_rows`
- `datacloud_cancel_query`
- `datacloud_metadata`

E' stato aggiunto `list_capabilities`, che espone i workflow Data Cloud supportati con area, alias, descrizione, input attesi e classe di rischio.

`plan_request` ora supporta piu' target Data Cloud:
- `data_streams`
- `validate_data_stream`
- `ingest_streaming_records`
- `ingest_bulk_csv`
- `inspect_data_model`
- `validate_identity_resolution`
- `validate_calculated_insight`
- `validate_data_action`

`query_datacloud` resta compatibile con `SALESFORCE_DATACLOUD_QUERY_URL`; se l'endpoint legacy non e' configurato, usa il nuovo flusso Query API basato su `SALESFORCE_DATACLOUD_API_URL`.

## Gap e ambiguità
Restano da validare su una sandbox Salesforce/Data Cloud reale:
- endpoint effettivi per tenant Data Cloud Query, Metadata e Ingestion API;
- payload esatti richiesti dai connector Ingestion API specifici della org;
- comportamento dei job bulk su file CSV reali e limiti tenant;
- permessi minimi OAuth e Data Cloud necessari per Query, Metadata e Ingestion;
- eventuali differenze di API version e path tra org.
