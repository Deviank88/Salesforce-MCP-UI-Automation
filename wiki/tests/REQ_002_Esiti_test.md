---
title: "Esiti test - REQ-002"
type: test_result
tags: [test, validation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_002_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-002"
status: tested
authority: validated_report
---
# Esiti test - REQ-002

Ambiente: Windows, Python 3.12.10.

Test eseguiti:
- `pytest -p no:cacheprovider --basetemp .testtmp`: 12 passed, 1 skipped.
- `$env:RUN_PLAYWRIGHT_SMOKE='1'; pytest -p no:cacheprovider --basetemp .testtmp_smoke tests\\test_browser_smoke.py`: 1 passed.
- `python -c \"import salesforce_mcp.server; print('server import ok')\"`: import server MCP riuscito.

Casi coperti:
- configurazione e dataclass `Settings`;
- guardrail azioni distruttive;
- shape output;
- assertion engine;
- API client non configurato;
- planner Data Streams;
- approvazione step supervisionato;
- rollback safe senza risorse gestite;
- smoke Playwright opzionale, saltato di default.
- smoke Playwright reale su pagina HTML locale, eseguito separatamente con Chromium headless.

Test non eseguito:
- test reale Salesforce/Data Cloud, perche richiede sandbox con Data Cloud abilitato, login, permessi e token OAuth/API.