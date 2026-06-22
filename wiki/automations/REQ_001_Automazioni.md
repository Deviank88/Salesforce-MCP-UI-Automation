---
title: "Automazioni - REQ-001"
type: automation
tags: [automation]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_001_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-001"
status: validated
authority: validated_report
---
# Automazioni - REQ-001

E' stata introdotta automazione browser via Playwright con profilo persistente locale in `.auth/<profile>`.

L'automazione non gestisce direttamente username, password, token applicativi, SSO o MFA. Il login resta manuale nella finestra browser e la sessione viene riutilizzata finche Salesforce la mantiene valida.

Le operazioni significative producono log e screenshot in `logs/`, directory esclusa da Git.