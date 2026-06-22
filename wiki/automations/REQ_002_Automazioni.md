---
title: "Automazioni - REQ-002"
type: automation
tags: [automation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_002_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-002"
status: validated
authority: validated_report
---
# Automazioni - REQ-002

E' stato aggiunto il workflow dichiarativo `configure_data_stream`.

Il workflow Data Streams MVP include:
- precheck sessione;
- snapshot prima della modifica;
- query baseline Salesforce/Data Cloud se dichiarate nella richiesta;
- step dry-run oppure step supervisionato `configure_data_stream`;
- query dopo la modifica;
- assertion record;
- raccomandazione finale.

Il workflow non esegue cancellazioni automatiche su Salesforce. Il rollback safe produce revisione tracciata e limita il cleanup alle risorse create o marcate come gestite dal run.