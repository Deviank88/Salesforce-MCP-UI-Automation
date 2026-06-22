---
title: "Automazioni - REQ-003"
type: automation
tags: [automation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_003_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-003"
status: validated
authority: validated_report
---
# Automazioni - REQ-003

E' stato introdotto un registry workflow in `salesforce_mcp/workflows.py`.

Nuovi workflow:
- `validate_data_stream`: valida metadata e query collegate a uno stream.
- `ingest_streaming_records`: valida payload e, dopo approvazione, invia record alla Streaming Ingestion API.
- `ingest_bulk_csv`: valida CSV, crea job bulk, carica CSV, chiude il job e legge lo stato.
- `inspect_data_model`: ispeziona metadata Data Cloud.
- `validate_identity_resolution`: valida output e profili collegati a identity resolution.
- `validate_calculated_insight`: valida metadata e risultati di Calculated Insights.
- `validate_data_action`: valida metadata e dati collegati a Data Actions.

Le scritture Data Cloud richiedono approval gate tramite `approve_step`. I workflow in dry-run non eseguono scritture.
