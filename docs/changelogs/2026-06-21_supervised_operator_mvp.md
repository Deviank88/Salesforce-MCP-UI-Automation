# Changelog - Operatore supervisionato MVP - 2026-06-21

## Aggiunto
- Execution engine supervisionato con run journal persistente.
- Planner `configure_data_stream` per Data Cloud Data Streams.
- Tool MCP: `plan_request`, `execute_plan`, `get_run_status`, `approve_step`, `rollback_run`.
- Tool MCP di verifica: `query_salesforce`, `query_datacloud`, `assert_records`, `compare_before_after`.
- API client configurabile tramite variabili ambiente.
- Assertion engine per record count, valori attesi, campi obbligatori, freshness e no-error check.
- Snapshot browser esteso con DOM opzionale, iframe e classificazione failure.
- Test per planner, journal, assertion, API client e rollback safe.

## Cambiato
- README e configurazione MCP esempio aggiornati con orchestrazione supervisionata e verification layer.
- `.gitignore` esteso per `runs/` e `.testtmp/`.

## Validazione
- `pytest -p no:cacheprovider --basetemp .testtmp`: 12 passed, 1 skipped.
- Smoke Playwright locale con `RUN_PLAYWRIGHT_SMOKE=1`: 1 passed.
- Import server MCP riuscito.

## Note
- La configurazione reale Data Streams resta supervisionata: il sistema apre e traccia il workflow, ma non esegue ancora cancellazioni o modifiche distruttive senza approvazione e implementazione specifica per sandbox.
