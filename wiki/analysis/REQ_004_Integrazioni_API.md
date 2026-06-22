---
title: "Integrazioni API - REQ-004"
type: integration
tags: [integration, api]
created: 2026-06-21
updated: 2026-06-21
sources: ["docs/reports/REQ_004_2026-06-21.md"]
client: "Interno"
project: "Salesforce MCP UI Automation"
request_id: "REQ-004"
status: validated
authority: validated_report
---
# Integrazioni API - REQ-004

Nuove variabili ambiente:
- `SALESFORCE_OAUTH_CLIENT_ID`
- `SALESFORCE_OAUTH_CLIENT_SECRET`
- `SALESFORCE_OAUTH_REDIRECT_URI`
- `SALESFORCE_OAUTH_SCOPES`

Endpoint Salesforce coinvolti:
- `/services/oauth2/authorize`
- `/services/oauth2/token`

Il flow supporta Connected App pubbliche con PKCE e Connected App confidenziali con client secret opzionale.
