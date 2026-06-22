# Changelog - Data Cloud API e Workflow Registry

Data: 2026-06-21
Request: REQ-003

## Aggiunto

- Tool MCP Data Cloud Query API: submit, status, rows e cancel.
- Tool MCP `datacloud_metadata` per metadata DLO, DMO, Calculated Insights, campi, chiavi e relazioni.
- Workflow registry con `list_capabilities` e `plan_request` multi-area.
- Workflow supervisionati per streaming ingestion, bulk CSV ingestion, data model inspection, identity resolution, calculated insights e data actions.
- Redazione configurabile dei campi sensibili nei run journal.

## Modificato

- `query_datacloud` resta compatibile con `SALESFORCE_DATACLOUD_QUERY_URL`, ma usa la Query API strutturata quando e' configurato `SALESFORCE_DATACLOUD_API_URL`.
- README e `mcp.example.json` documentano i nuovi endpoint e le variabili ambiente.

## Validazione

- `pytest -p no:cacheprovider --basetemp .testtmp_final`: 20 passed, 1 skipped.
- `python -m compileall salesforce_mcp`: completato.
- `python -c "import salesforce_mcp.server; print('server import ok')"`: import server riuscito.
