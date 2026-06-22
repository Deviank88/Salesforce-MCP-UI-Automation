---
title: "Esiti test - REQ-003"
type: test_result
tags: [test, validation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_003_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-003"
status: tested
authority: validated_report
---
# Esiti test - REQ-003

Ambiente: Windows, Python 3.12.10.

Test eseguiti:
- `pytest -p no:cacheprovider --basetemp .testtmp_quality tests\\test_api_client.py tests\\test_execution.py`: 12 passed.
- `python -m compileall salesforce_mcp`: compilazione moduli completata.
- `pytest -p no:cacheprovider --basetemp .testtmp_final`: 20 passed, 1 skipped.
- `python -c "import salesforce_mcp.server; print('server import ok')"`: import server MCP riuscito.

Casi coperti:
- path e payload Query API;
- filtri Metadata API;
- base URL Ingestion API;
- capability registry;
- planner multi-workflow;
- approval gate per streaming ingestion;
- piano bulk CSV completo con validate, create, upload, close e status;
- redazione campi sensibili nel run journal;
- regressione su guardrail, assertion engine e output esistenti.

Test non eseguito:
- test reale Salesforce/Data Cloud, perche richiede sandbox con Data Cloud abilitato, endpoint tenant, token OAuth/API, login e permessi.
