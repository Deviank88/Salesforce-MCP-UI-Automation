# Changelog - Playwright Auth Bridge

Data: 2026-06-21
Request: REQ-004

## Aggiunto

- Modulo `salesforce_mcp/auth.py` con token store runtime in memoria.
- Bridge Playwright per leggere il cookie Salesforce `sid` tramite API Playwright.
- Flow OAuth Authorization Code + PKCE con callback localhost e refresh token runtime.
- Tool MCP `browser_auth_status`, `use_browser_session_token`, `start_oauth_token_flow`, `refresh_oauth_token` e `clear_runtime_tokens`.
- Precedenza token runtime > variabili ambiente per Salesforce REST e Data Cloud API.
- Variabili OAuth in `.env.example`, `README.md` e `mcp.example.json`.

## Sicurezza

- I token non vengono scritti su disco.
- Gli output dei tool auth mostrano solo valori mascherati.
- Il refresh token non viene ricavato dalla sessione UI Salesforce; richiede Connected App OAuth.

## Validazione

- `pytest -p no:cacheprovider --basetemp .testtmp_auth tests\\test_auth.py tests\\test_api_client.py tests\\test_config.py`: 13 passed.
- `python -m compileall salesforce_mcp`: completato.
- `pytest -p no:cacheprovider --basetemp .testtmp_final`: 28 passed, 1 skipped.
- `python -c "import salesforce_mcp.server; print('server import ok')"`: import server riuscito.
