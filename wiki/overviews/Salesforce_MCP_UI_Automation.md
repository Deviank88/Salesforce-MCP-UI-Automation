---
title: "Salesforce MCP UI Automation"
type: overview
tags: [salesforce, mcp, playwright, data-cloud]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_001_2026-06-21.md", "docs/reports/REQ_002_2026-06-21.md", "docs/reports/REQ_003_2026-06-21.md", "docs/reports/REQ_004_2026-06-21.md", "docs/changelogs/2026-06-21_salesforce_mcp_initial.md", "docs/changelogs/2026-06-21_supervised_operator_mvp.md", "docs/changelogs/2026-06-21_datacloud_api_registry.md", "docs/changelogs/2026-06-21_playwright_auth_bridge.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-004"
status: implemented
authority: validated_report
---
# Salesforce MCP UI Automation

Questa pagina raccoglie la conoscenza del progetto Salesforce MCP UI Automation, nato per controllare Salesforce via browser Playwright persistente attraverso un server MCP locale, evoluto verso un operatore supervisionato, ampliato con capability Data Cloud API-first e completato con auth bridge runtime.

## Percorso di lettura

### Fondazione browser MCP

- [[REQ_001_richiesta]] descrive obiettivo, contesto e gap iniziali.
- [[REQ_001_Requisiti]] sintetizza i tool MCP browser e il primo perimetro Data Cloud.
- [[REQ_001_implementazione]] documenta architettura Playwright, integrazione MCP e guardrail iniziali.
- [[REQ_001_Automazioni]] spiega sessione Playwright persistente, log e screenshot.
- [[REQ_001_Integrazioni_API]] descrive l'interfaccia MCP base.
- [[REQ_001_Esiti_test]] registra i test iniziali.
- [[REQ_001_Changelog_e_rilascio]] punta alla nota di rilascio iniziale.

### Operatore supervisionato

- [[REQ_002_richiesta]] descrive l'evoluzione verso run supervisionati, test dati e cleanup tracciato.
- [[REQ_002_Requisiti]] sintetizza orchestrazione, verifica dati e workflow Data Streams MVP.
- [[REQ_002_implementazione]] documenta execution engine, run journal, API client e assertion engine.
- [[REQ_002_Automazioni]] spiega il workflow dichiarativo `configure_data_stream`.
- [[REQ_002_Integrazioni_API]] descrive query Salesforce, query Data Cloud configurabile e output di verifica.
- [[REQ_002_Esiti_test]] registra i test della milestone supervisionata.
- [[REQ_002_Changelog_e_rilascio]] punta alla nota di rilascio dell'MVP supervisionato.

### Estensione Data Cloud API e registry

- [[REQ_003_richiesta]] descrive l'obiettivo di estendere l'MCP con Query API, Metadata API, ingestion e validazioni avanzate.
- [[REQ_003_Requisiti]] elenca i nuovi tool MCP, `list_capabilities` e i target supportati da `plan_request`.
- [[REQ_003_implementazione]] documenta registry workflow, client Data Cloud e redazione journal.
- [[REQ_003_Automazioni]] descrive i workflow `validate_data_stream`, `ingest_streaming_records`, `ingest_bulk_csv`, `inspect_data_model`, `validate_identity_resolution`, `validate_calculated_insight` e `validate_data_action`.
- [[REQ_003_Integrazioni_API]] descrive Query API, Metadata API, Ingestion API e variabili ambiente.
- [[REQ_003_Esiti_test]] registra test mirati, suite completa e gap di validazione reale.
- [[REQ_003_Changelog_e_rilascio]] punta alla nota di rilascio della milestone.

### Auth bridge Playwright e OAuth

- [[REQ_004_richiesta]] descrive l'obiettivo di collegare sessione Playwright, token runtime e API client.
- [[REQ_004_Requisiti]] elenca i tool `browser_auth_status`, `use_browser_session_token`, `start_oauth_token_flow`, `refresh_oauth_token` e `clear_runtime_tokens`.
- [[REQ_004_implementazione]] documenta token store runtime, cookie `sid`, OAuth Authorization Code + PKCE e mascheramento output.
- [[REQ_004_Integrazioni_API]] descrive variabili OAuth e endpoint `/services/oauth2/authorize` e `/services/oauth2/token`.
- [[REQ_004_Esiti_test]] registra test PKCE, cookie sessione, precedenza token runtime e regressione completa.
- [[REQ_004_Changelog_e_rilascio]] punta alla nota di rilascio della milestone.

## Stato attuale

Il progetto dispone di una base eseguibile con server MCP Python, controllo browser Playwright, run journal, guardrail, verification layer, rollback supervisionato, capability Data Cloud API-first e auth bridge runtime.

Lo stato corrente include Query API strutturata, Metadata API, workflow ingestion streaming e bulk CSV, workflow registry, discovery capability, validazioni Data Cloud avanzate, uso del cookie `sid` Playwright come session token runtime e OAuth Authorization Code + PKCE per access/refresh token in memoria. La prossima validazione necessaria resta il collegamento a una sandbox Salesforce reale con Data Cloud abilitato per confermare cookie REST, Connected App, scope OAuth, endpoint tenant, payload Ingestion API, limiti bulk e comportamento su dati reali.