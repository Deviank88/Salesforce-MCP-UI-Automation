---
title: "Implementazione - REQ-002"
type: implementation
tags: [implementation, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_002_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-002"
status: implemented
authority: validated_report
---
# Implementazione - REQ-002

## Sintesi implementativa
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

## Data model
Nessuna modifica al data model Salesforce.

E' stato introdotto un data model locale per i run journal:
- `RunJournal`: run_id, richiesta, area target, workflow, dry_run, status, recommendation, steps, resources.
- `RunStep`: id, tipo, descrizione, input, status, approvazione, tentativi, output, errore, risorse.

I journal vengono salvati in `runs/<run_id>/run.json`, esclusi da Git perche possono contenere dati operativi.

## Automazioni
E' stato aggiunto il workflow dichiarativo `configure_data_stream`.

Il workflow Data Streams MVP include:
- precheck sessione;
- snapshot prima della modifica;
- query baseline Salesforce/Data Cloud se dichiarate nella richiesta;
- step dry-run oppure step supervisionato `configure_data_stream`;
- query dopo la modifica;
- assertion record;
- raccomandazione finale.

Il workflow non esegue cancellazioni automatiche su Salesforce. Il rollback safe produce revisione tracciata e limita il cleanup alle risorse create o marcate come gestite dal run.

## Integrazioni/API
E' stato aggiunto `SalesforceApiClient` basato su librerie standard Python.

Configurazione Salesforce standard:
- `SALESFORCE_INSTANCE_URL`
- `SALESFORCE_ACCESS_TOKEN`
- `SALESFORCE_API_VERSION`

Configurazione Data Cloud:
- `SALESFORCE_DATACLOUD_QUERY_URL`
- `SALESFORCE_DATACLOUD_ACCESS_TOKEN`

L'endpoint Data Cloud e' intenzionalmente configurabile per evitare assunzioni non verificate su URL e setup specifici dell'org.

## UI/UX
Non e' stata introdotta una UI proprietaria.

L'esperienza MCP e' stata estesa con tool supervisionati: l'utente puo pianificare, eseguire, approvare step, verificare dati, confrontare baseline e preparare rollback.

## Permessi/Sicurezza
Le credenziali non vengono salvate nel codice. Token e URL API vengono letti da variabili ambiente o `.env` locale escluso da Git.

I run journal, log, screenshot, profili browser e file temporanei sono esclusi da Git.

Le azioni supervisionate che modificano Data Streams richiedono approvazione step. Il rollback dangerous richiede `confirm_dangerous=true`.