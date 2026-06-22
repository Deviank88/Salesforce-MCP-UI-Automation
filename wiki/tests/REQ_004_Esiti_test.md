---
title: "Esiti test - REQ-004"
type: test_result
tags: [test, validation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_004_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-004"
status: tested
authority: validated_report
---
# Esiti test - REQ-004

Ambiente: Windows, Python 3.12.10.

Test eseguiti:
- `pytest -p no:cacheprovider --basetemp .testtmp_auth tests\\test_auth.py tests\\test_api_client.py tests\\test_config.py`: 13 passed.
- `python -m compileall salesforce_mcp`: compilazione moduli completata.
- `pytest -p no:cacheprovider --basetemp .testtmp_final`: 28 passed, 1 skipped.
- `python -c "import salesforce_mcp.server; print('server import ok')"`: import server MCP riuscito.

Casi coperti:
- generazione PKCE verifier/challenge;
- selezione cookie `sid` per dominio Salesforce;
- authorize URL OAuth con PKCE;
- token exchange con `code_verifier`;
- output mascherati senza token in chiaro;
- precedenza token runtime per Salesforce REST;
- precedenza token runtime per Data Cloud API;
- clear runtime tokens;
- regressione API, workflow, guardrail e output esistenti.

Test non eseguito:
- test reale OAuth su Salesforce, perche richiede Connected App configurata, redirect URI localhost autorizzato, login interattivo e permessi org.
