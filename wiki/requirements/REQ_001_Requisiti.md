---
title: "Requisiti - REQ-001"
type: requirement
tags: [requirement, functional]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_001_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-001"
status: validated
authority: validated_report
---
# Requisiti - REQ-001

E' stato creato un server MCP Python avviabile con `python -m salesforce_mcp` o tramite entrypoint `salesforce-mcp`.

Il server espone tool generici per controllare Salesforce via browser Playwright:
- `open_org` per aprire una org Salesforce configurata o passata a runtime.
- `snapshot` per leggere URL, titolo, testo visibile, screenshot opzionale, warning e azioni suggerite.
- `click`, `fill`, `select` e `wait_for` per interagire con la UI.
- `search_setup` per aprire Salesforce Setup e usare Quick Find.
- `close_browser` per chiudere il contesto browser persistente.

Sono stati aggiunti tool orientati a Data Cloud:
- `open_datacloud_area` per ricercare aree note come Data Streams, Data Spaces, Identity Resolution, Calculated Insights e Data Actions.
- `diagnose_datacloud` per raccogliere uno snapshot diagnostico e segnalare possibili problemi di login, pagina non Data Cloud o permessi.