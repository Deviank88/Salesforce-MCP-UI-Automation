---
title: "Requisiti - REQ-003"
type: requirement
tags: [requirement, functional]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_003_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-003"
status: validated
authority: validated_report
---
# Requisiti - REQ-003

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
