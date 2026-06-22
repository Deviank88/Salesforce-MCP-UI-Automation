---
title: "Integrazioni API - REQ-001"
type: integration
tags: [integration, api]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_001_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-001"
status: validated
authority: validated_report
---
# Integrazioni API - REQ-001

E' stata implementata un'integrazione MCP locale basata su `mcp.server.fastmcp.FastMCP`.

L'interfaccia pubblica e' composta dai tool MCP elencati nelle modifiche funzionali. Gli output seguono una forma stabile:
- `url`
- `title`
- `visible_text`
- `screenshot_path`
- `warnings`
- `next_suggested_actions`

Il progetto include `mcp.example.json` come base per configurare un client MCP con comando `python -m salesforce_mcp` e variabili ambiente Salesforce.