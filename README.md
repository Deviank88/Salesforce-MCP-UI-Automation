# Salesforce MCP UI Automation

MCP server Python per automatizzare Salesforce via browser Playwright con sessione persistente. L'MVP parte da Data Cloud, ma i tool sono generici abbastanza da coprire Setup, Marketing Cloud Growth, Agentforce e altre aree configurabili solo da UI.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m playwright install chromium
Copy-Item .env.example .env
```

Aggiorna `.env` con l'URL della tua org e, se usi le API Data Cloud, con endpoint tenant e token:

```ini
SALESFORCE_ORG_URL=https://your-domain.my.salesforce.com
SALESFORCE_INSTANCE_URL=https://your-domain.my.salesforce.com
SALESFORCE_ACCESS_TOKEN=
SALESFORCE_API_VERSION=61.0
SALESFORCE_DATACLOUD_API_URL=https://your-data-cloud-tenant.example.com
SALESFORCE_DATACLOUD_INGESTION_URL=https://your-ingestion-tenant.example.com
SALESFORCE_DATACLOUD_QUERY_URL=
SALESFORCE_DATACLOUD_ACCESS_TOKEN=
SALESFORCE_JOURNAL_REDACT_FIELDS=token,password,secret,access_token,refresh_token,authorization
SALESFORCE_OAUTH_CLIENT_ID=
SALESFORCE_OAUTH_CLIENT_SECRET=
SALESFORCE_OAUTH_REDIRECT_URI=http://localhost:1717/oauth/callback
SALESFORCE_OAUTH_SCOPES=api refresh_token
SALESFORCE_PROFILE=default
SALESFORCE_HEADLESS=false
```

## Avvio MCP

```powershell
python -m salesforce_mcp
```

Oppure, dopo installazione editable:

```powershell
salesforce-mcp
```

Per configurare un client MCP, parti da `mcp.example.json` e aggiorna `SALESFORCE_ORG_URL`.

## Autenticazione

Il server non salva username, password o token applicativi. Al primo uso apre Chromium con profilo persistente in `.auth/<profile>`. Completa login, SSO e MFA manualmente. Le chiamate successive riusano la stessa sessione finche Salesforce la mantiene valida.

Per usare le API senza copiare manualmente `SALESFORCE_ACCESS_TOKEN`, puoi chiamare `use_browser_session_token` dopo il login Playwright: il tool legge il cookie Salesforce `sid` tramite API Playwright e lo usa come token runtime in memoria. Il refresh token non viene estratto dalla normale sessione browser; per ottenerlo usa `start_oauth_token_flow` con una Connected App configurata per Authorization Code + PKCE e scope `refresh_token`.

## Tool Esposti

### Browser e Setup

- `open_org`: apre l'org configurata o un URL specifico.
- `snapshot`: restituisce URL, titolo, testo visibile, screenshot opzionale, DOM opzionale, iframe e suggerimenti.
- `click`: clicca per testo, selector CSS o ruolo accessibile.
- `fill`: compila un input per label/placeholder/testo o selector CSS.
- `select`: seleziona un valore in un campo select.
- `wait_for`: attende caricamenti, testo o selector.
- `search_setup`: apre Setup e cerca una voce.
- `open_datacloud_area`: apre o ricerca aree Data Cloud note.
- `diagnose_datacloud`: raccoglie uno snapshot diagnostico orientato a Data Cloud.
- `close_browser`: chiude browser e profilo persistente.

### Autenticazione API

- `browser_auth_status`: verifica sessione Playwright e token runtime senza mostrare segreti.
- `use_browser_session_token`: usa il cookie `sid` Salesforce come token runtime per `query_salesforce`.
- `start_oauth_token_flow`: avvia OAuth Authorization Code + PKCE in Playwright e salva access/refresh token in memoria.
- `refresh_oauth_token`: rinnova l'access token runtime usando il refresh token.
- `clear_runtime_tokens`: svuota i token runtime in memoria.

### Orchestrazione supervisionata

- `list_capabilities`: elenca workflow Data Cloud supportati, input attesi e classe di rischio.
- `plan_request`: crea un run journal per Data Streams, metadata, ingestion e validazioni Data Cloud.
- `execute_plan`: esegue il piano fino a completamento, errore o richiesta approvazione.
- `get_run_status`: legge lo stato completo di un run.
- `approve_step`: approva uno step supervisionato.
- `rollback_run`: prepara rollback safe/manual_review/dangerous sulle sole risorse tracciate.

### Verifica dati

- `query_salesforce`: esegue SOQL usando token runtime o `SALESFORCE_INSTANCE_URL` e `SALESFORCE_ACCESS_TOKEN`.
- `query_datacloud`: esegue query Data Cloud su endpoint configurabile `SALESFORCE_DATACLOUD_QUERY_URL`.
- `datacloud_submit_query`: invia una query SQL alla Data Cloud Query API.
- `datacloud_query_status`: legge lo stato di una query Data Cloud.
- `datacloud_query_rows`: legge righe paginabili per una query Data Cloud.
- `datacloud_cancel_query`: cancella una query Data Cloud in esecuzione.
- `datacloud_metadata`: legge metadata Data Cloud per DLO, DMO, Calculated Insights, campi, chiavi e relazioni.
- `assert_records`: valida record count, campi obbligatori, valori attesi, freshness e assenza errori.
- `compare_before_after`: confronta evidenze query raccolte nel run journal.

Workflow supportati da `plan_request`:

- `data_streams`: configurazione supervisionata via browser.
- `validate_data_stream`: validazione metadata/query di uno stream.
- `ingest_streaming_records`: validazione e invio JSON via Streaming Ingestion API.
- `ingest_bulk_csv`: validazione CSV, creazione job, upload, close e status Bulk Ingestion API.
- `inspect_data_model`: ispezione DLO, DMO, relazioni, chiavi e key qualifier.
- `validate_identity_resolution`: validazione output identity resolution.
- `validate_calculated_insight`: validazione metadata e risultati Calculated Insight.
- `validate_data_action`: validazione dati e metadata collegati a Data Actions.

I run journal sono salvati in `runs/<run_id>/run.json`, esclusi da Git perche possono contenere dati operativi e screenshot correlati. I campi configurati in `SALESFORCE_JOURNAL_REDACT_FIELDS` vengono mascherati prima della scrittura.

## Guardrail

Le azioni potenzialmente distruttive richiedono `confirm_dangerous=true`. Screenshot e log operativi sono salvati in `logs/`, escluso da Git insieme a `.auth/` e `.env`.

Le scritture Data Cloud dei workflow ingestion richiedono approvazione step tramite `approve_step`. Gli endpoint Data Cloud restano configurabili per tenant: usa `SALESFORCE_DATACLOUD_API_URL` per Query/Metadata API, `SALESFORCE_DATACLOUD_INGESTION_URL` per Ingestion API e `SALESFORCE_DATACLOUD_QUERY_URL` solo come endpoint legacy compatibile per `query_datacloud`.

## Test

```powershell
pytest
```

I test automatici validano configurazione, guardrail, journal, planner, assertion engine e shape degli output. Se la directory temp utente non e' scrivibile, usa:

```powershell
pytest -p no:cacheprovider --basetemp .testtmp
```

Il test reale su Salesforce resta manuale perche richiede una org e login interattivo.

Per validare anche Chromium/Playwright su una pagina HTML locale:

```powershell
$env:RUN_PLAYWRIGHT_SMOKE="1"
pytest tests/test_browser_smoke.py
```
