---
title: "Esiti test - REQ-001"
type: test_result
tags: [test, validation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_001_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-001"
status: tested
authority: validated_report
---
# Esiti test - REQ-001

Ambiente: Windows, Python 3.12.10.

Test automatici eseguiti:
- `pytest -p no:cacheprovider`: 6 passed, 1 skipped.
- `$env:RUN_PLAYWRIGHT_SMOKE='1'; pytest -p no:cacheprovider tests/test_browser_smoke.py`: 1 passed.
- `python -c "import salesforce_mcp.server; print('server import ok')"`: import server MCP riuscito.
- `python -c "import mcp, playwright; print('dependencies ok')"`: dipendenze principali disponibili.

Il test smoke Playwright apre Chromium headless su una pagina HTML locale, compila un campo, clicca un bottone e salva uno screenshot in una directory temporanea.

Test non eseguito:
- Test reale su Salesforce/Data Cloud non eseguito perche richiede org Salesforce, login interattivo, SSO/MFA e permessi Data Cloud.