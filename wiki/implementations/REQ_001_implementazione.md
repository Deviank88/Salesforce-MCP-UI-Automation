---
title: "Implementazione - REQ-001"
type: implementation
tags: [implementation, validated]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_001_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-001"
status: implemented
authority: validated_report
---
# Implementazione - REQ-001

## Sintesi implementativa
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

## Data model
Nessuna modifica al data model Salesforce. Il progetto non crea oggetti, campi, relazioni o migrazioni dati.

## Automazioni
E' stata introdotta automazione browser via Playwright con profilo persistente locale in `.auth/<profile>`.

L'automazione non gestisce direttamente username, password, token applicativi, SSO o MFA. Il login resta manuale nella finestra browser e la sessione viene riutilizzata finche Salesforce la mantiene valida.

Le operazioni significative producono log e screenshot in `logs/`, directory esclusa da Git.

## Integrazioni/API
E' stata implementata un'integrazione MCP locale basata su `mcp.server.fastmcp.FastMCP`.

L'interfaccia pubblica e' composta dai tool MCP elencati nelle modifiche funzionali. Gli output seguono una forma stabile:
- `url`
- `title`
- `visible_text`
- `screenshot_path`
- `warnings`
- `next_suggested_actions`

Il progetto include `mcp.example.json` come base per configurare un client MCP con comando `python -m salesforce_mcp` e variabili ambiente Salesforce.

## UI/UX
Non e' stata realizzata una UI applicativa propria. L'esperienza utente e' la UI Salesforce controllata tramite Playwright.

Il browser usa una sessione persistente, viewport configurabile e modalita headless disattivata di default per consentire login interattivo, SSO e MFA.

## Permessi/Sicurezza
Sono stati aggiunti guardrail per azioni potenzialmente distruttive. Termini come delete, remove, deactivate, disable, reset, elimina e rimuovi bloccano l'azione se non viene passato `confirm_dangerous=true`.

`.auth/`, `.env`, `logs/`, cache Python e artefatti di build sono esclusi da Git tramite `.gitignore`.

Il server non salva credenziali esplicite. La sicurezza effettiva dipende dai permessi Salesforce dell'utente autenticato nel profilo browser.