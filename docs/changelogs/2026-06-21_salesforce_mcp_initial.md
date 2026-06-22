# Changelog - Salesforce MCP UI Automation - 2026-06-21

## Aggiunto
- Progetto Python MCP per automazione Salesforce via Playwright.
- Sessione Chromium persistente in `.auth/<profile>`.
- Tool MCP generici per navigazione, snapshot, click, fill, select, wait e ricerca Setup.
- Tool iniziali Data Cloud: apertura aree note e diagnostica pagina.
- Guardrail per azioni potenzialmente distruttive.
- Output standardizzato con URL, titolo, testo visibile, screenshot, warning e azioni suggerite.
- Documentazione `README.md`, `.env.example` e `mcp.example.json`.
- Test automatici e smoke test Playwright opzionale.

## Validazione
- `pytest -p no:cacheprovider`: 6 passed, 1 skipped.
- Smoke Playwright locale: 1 passed.

## Note
- Il test reale su Salesforce richiede org cliente, login interattivo e permessi Data Cloud.
