---
title: "Requisiti - REQ-004"
type: requirement
tags: [requirement, functional]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_004_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-004"
status: validated
authority: validated_report
---
# Requisiti - REQ-004

E' stato aggiunto un auth bridge runtime tra Playwright e API client.

Nuovi tool MCP:
- `browser_auth_status`: verifica sessione browser, cookie `sid` e token runtime senza esporre segreti.
- `use_browser_session_token`: legge il cookie Salesforce `sid` dal context Playwright e lo usa come session token runtime per `query_salesforce`.
- `start_oauth_token_flow`: avvia OAuth Authorization Code + PKCE nella pagina Playwright, riceve callback localhost, scambia il code e salva access token e refresh token in memoria.
- `refresh_oauth_token`: rinnova l'access token runtime usando il refresh token in memoria.
- `clear_runtime_tokens`: svuota i token runtime Salesforce e Data Cloud.

Il client API ora usa la precedenza token runtime > variabili ambiente. `query_salesforce` puo' funzionare con token derivato dalla sessione Playwright o con token OAuth runtime. Le API Data Cloud possono usare token OAuth runtime prima del fallback su `SALESFORCE_DATACLOUD_ACCESS_TOKEN`.
