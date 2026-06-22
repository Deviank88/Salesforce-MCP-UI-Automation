---
title: "Richiesta REQ-002"
type: request
tags: [request, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_002_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-002"
status: validated
authority: validated_report
---
# Richiesta REQ-002

## Contesto
Obiettivo: Implementare il piano operativo per rendere l'MCP un operatore supervisionato con run journal, orchestration tool, verification layer e workflow Data Streams MVP.

File o fonti collegate:
- salesforce_mcp/execution.py
- salesforce_mcp/journal.py
- salesforce_mcp/workflows.py
- salesforce_mcp/api_client.py
- salesforce_mcp/assertions.py
- salesforce_mcp/browser.py
- salesforce_mcp/server.py
- tests/test_execution.py
- tests/test_assertions.py
- tests/test_api_client.py
- README.md
- mcp.example.json

## Modifiche funzionali
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

## Gap e ambiguità
Restano da validare su sandbox reale:
- endpoint Data Cloud Query effettivo e payload richiesto per la specifica org;
- strategia OAuth definitiva per Salesforce e Data Cloud;
- selector UI reali per creare/modificare Data Streams;
- cleanup automatico specifico per Data Streams;
- criteri di successo cliente per record, mapping e freshness.