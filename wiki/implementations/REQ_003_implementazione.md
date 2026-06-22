---
title: "Implementazione - REQ-003"
type: implementation
tags: [implementation, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_003_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-003"
status: implemented
authority: validated_report
---
# Implementazione - REQ-003

## Sintesi implementativa
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

## Data model
Nessuna modifica al data model Salesforce.

E' stato esteso il data model locale dei run journal con step e input per workflow Data Cloud aggiuntivi. Non sono stati introdotti nuovi oggetti Salesforce, campi, relazioni o migrazioni dati.

## Automazioni
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

## Integrazioni/API
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

## UI/UX
Nessuna UI proprietaria introdotta.

L'esperienza MCP migliora tramite discovery (`list_capabilities`) e piani supervisionati piu' espliciti. Le aree che richiedono UI Salesforce restano gestite via Playwright e approval gate.

## Permessi/Sicurezza
Le azioni distruttive restano protette da `confirm_dangerous=true`.

Le scritture ingestion richiedono approvazione step. I run journal vengono salvati in `runs/<run_id>/run.json`, ma i campi configurati in `SALESFORCE_JOURNAL_REDACT_FIELDS` vengono mascherati prima della scrittura.

Token e URL API restano configurati via variabili ambiente o `.env` locale escluso da Git.
