---
title: "Implementazione - REQ-004"
type: implementation
tags: [implementation, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_004_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-004"
status: implemented
authority: validated_report
---
# Implementazione - REQ-004

## Sintesi implementativa
E' stato aggiunto un auth bridge runtime tra Playwright e API client.

Nuovi tool MCP:
- `browser_auth_status`: verifica sessione browser, cookie `sid` e token runtime senza esporre segreti.
- `use_browser_session_token`: legge il cookie Salesforce `sid` dal context Playwright e lo usa come session token runtime per `query_salesforce`.
- `start_oauth_token_flow`: avvia OAuth Authorization Code + PKCE nella pagina Playwright, riceve callback localhost, scambia il code e salva access token e refresh token in memoria.
- `refresh_oauth_token`: rinnova l'access token runtime usando il refresh token in memoria.
- `clear_runtime_tokens`: svuota i token runtime Salesforce e Data Cloud.

Il client API ora usa la precedenza token runtime > variabili ambiente. `query_salesforce` puo' funzionare con token derivato dalla sessione Playwright o con token OAuth runtime. Le API Data Cloud possono usare token OAuth runtime prima del fallback su `SALESFORCE_DATACLOUD_ACCESS_TOKEN`.

## Data model
Nessuna modifica al data model Salesforce.

E' stato aggiunto un data model runtime in memoria:
- `TokenBundle`: access token, refresh token opzionale, instance URL, token type, source, issued_at, expires_in, scope e domain.
- `RuntimeTokenStore`: token Salesforce e token Data Cloud in memoria per il processo MCP.

Questi dati non vengono salvati nei run journal.

## Automazioni
Nessuna nuova automazione Salesforce.

E' stato aggiunto un flusso locale OAuth:
- generazione PKCE verifier/challenge;
- apertura authorize URL nella sessione Playwright;
- callback localhost temporanea;
- scambio code su `/services/oauth2/token`;
- refresh token flow su `/services/oauth2/token`.

## Integrazioni/API
Nuove variabili ambiente:
- `SALESFORCE_OAUTH_CLIENT_ID`
- `SALESFORCE_OAUTH_CLIENT_SECRET`
- `SALESFORCE_OAUTH_REDIRECT_URI`
- `SALESFORCE_OAUTH_SCOPES`

Endpoint Salesforce coinvolti:
- `/services/oauth2/authorize`
- `/services/oauth2/token`

Il flow supporta Connected App pubbliche con PKCE e Connected App confidenziali con client secret opzionale.

## UI/UX
Non e' stata introdotta una UI proprietaria.

L'utente completa login, SSO e MFA nella finestra Playwright persistente. Il flow OAuth riusa la sessione Playwright e mostra la pagina autorizzativa Salesforce quando necessario.

## Permessi/Sicurezza
I token restano solo in memoria e non vengono scritti su disco.

Gli output dei tool auth sono mascherati: indicano presenza, source, dominio, instance URL e stato, ma non espongono token in chiaro.

Il refresh token non viene recuperato dalla normale sessione UI Salesforce, perche non e' garantito che sia disponibile nel browser. Il refresh token richiede una Connected App configurata con scope `refresh_token` o equivalente offline access.
