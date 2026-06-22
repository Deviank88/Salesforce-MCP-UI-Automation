---
title: "Requisiti - REQ-002"
type: requirement
tags: [requirement, functional]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_002_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-002"
status: validated
authority: validated_report
---
# Requisiti - REQ-002

E' stato introdotto un execution engine supervisionato che trasforma una richiesta utente in un run journal tracciato.

Nuovi tool MCP di orchestrazione:
- `plan_request(request, target_area, dry_run=true)` crea un piano Data Streams e salva `runs/<run_id>/run.json`.
- `execute_plan(run_id, max_attempts=3)` esegue step fino a completamento, errore o richiesta approvazione.
- `get_run_status(run_id)` restituisce lo stato completo del run.
- `approve_step(run_id, step_id)` approva uno step supervisionato.
- `rollback_run(run_id, mode=\"safe\")` prepara rollback tracciato sulle sole risorse gestite dal run.

Nuovi tool MCP di verifica:
- `query_salesforce(soql)` esegue query SOQL usando configurazione OAuth da variabili ambiente.
- `query_datacloud(sql_or_query)` esegue query Data Cloud su endpoint configurabile.
- `assert_records(assertion, records)` valida count, valori attesi, campi obbligatori, freshness e assenza errori.
- `compare_before_after(run_id)` confronta evidenze raccolte prima e dopo la modifica.

Lo snapshot browser ora puo includere DOM, iframe e classificazione failure di base.