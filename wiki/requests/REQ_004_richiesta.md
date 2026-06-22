---
title: "Richiesta REQ-004"
type: request
tags: [request, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_004_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-004"
status: validated
authority: validated_report
---
# Richiesta REQ-004

## Contesto
Obiettivo: Implementare un auth bridge sicuro tra sessione Playwright, token runtime, Salesforce API e Data Cloud API con OAuth Authorization Code + PKCE.

File o fonti collegate:
- salesforce_mcp/auth.py
- salesforce_mcp/browser.py
- salesforce_mcp/api_client.py
- salesforce_mcp/config.py
- salesforce_mcp/server.py
- tests/test_auth.py
- tests/test_api_client.py
- .env.example
- README.md
- mcp.example.json
- docs/changelogs/2026-06-21_playwright_auth_bridge.md

## Modifiche funzionali
E' stato aggiunto un auth bridge runtime tra Playwright e API client.

Nuovi tool MCP:
- `browser_auth_status`: verifica sessione browser, cookie `sid` e token runtime senza esporre segreti.
- `use_browser_session_token`: legge il cookie Salesforce `sid` dal context Playwright e lo usa come session token runtime per `query_salesforce`.
- `start_oauth_token_flow`: avvia OAuth Authorization Code + PKCE nella pagina Playwright, riceve callback localhost, scambia il code e salva access token e refresh token in memoria.
- `refresh_oauth_token`: rinnova l'access token runtime usando il refresh token in memoria.
- `clear_runtime_tokens`: svuota i token runtime Salesforce e Data Cloud.

Il client API ora usa la precedenza token runtime > variabili ambiente. `query_salesforce` puo' funzionare con token derivato dalla sessione Playwright o con token OAuth runtime. Le API Data Cloud possono usare token OAuth runtime prima del fallback su `SALESFORCE_DATACLOUD_ACCESS_TOKEN`.

## Gap e ambiguità
Restano da validare su una org Salesforce reale:
- uso effettivo del cookie `sid` come bearer token REST con le policy della org;
- configurazione Connected App per Authorization Code + PKCE;
- scope OAuth necessari per Data Cloud API nello specifico tenant;
- comportamento SSO/MFA durante authorize URL;
- durata del token runtime e rinnovo in sessioni MCP lunghe.
