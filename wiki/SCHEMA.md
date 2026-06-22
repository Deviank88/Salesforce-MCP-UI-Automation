# Wiki Schema and Conventions

> This file defines the structure, workflows, and quality standards for this wiki.
> Read it at the start of every session. Update it when conventions change.

---

## Lingua

**Tutte le pagine wiki devono essere scritte in italiano.**
I campi di frontmatter (`title`, `tags`, ecc.) rimangono nei loro formati tecnici (es. date ISO, lowercase-with-hyphens per i tag), ma tutto il testo libero — titoli, contenuto, descrizioni, commenti — deve essere in italiano.

---

## Directory Layout

```
{project-root}/
├── docs/         # Source documents and generated output
│   ├── client/       # Documenti forniti dal cliente
│   ├── transcripts/  # Transcript meeting e sintesi NotebookLM
│   ├── reports/      # Development report validati
│   ├── changelogs/   # Changelog tecnici/funzionali
│   ├── normalized/   # Fonti convertite in markdown
│   ├── deliverables/ # Documenti finali e DOCX
│   └── assets/       # Downloaded images (optional)
└── wiki/         # LLM-maintained knowledge base
    ├── SCHEMA.md # This file
    ├── index.md  # Master index of all pages
    ├── log.md    # Operation log (append-only)
    ├── entities/ # Named things: people, companies, products
    ├── concepts/ # Ideas, techniques, patterns
    ├── summaries/# Per-source document summaries
    ├── comparisons/ # Side-by-side analysis of multiple things
    ├── overviews/   # High-level landscape pages
    ├── analysis/    # Reasoned arguments and synthesis
    ├── requests/    # Richieste validate end-to-end
    ├── requirements/# Requisiti
    ├── implementations/# Sintesi implementative
    ├── tests/       # Esiti test
    ├── releases/    # Rilasci/changelog
    ├── data-model/  # Data model
    └── automations/ # Automazioni
```

---

## Required Frontmatter

Every wiki page MUST begin with YAML frontmatter:

```yaml
---
title: "Human-readable page title"
type: entity | concept | summary | comparison | overview | analysis | meeting_note | client_source | candidate_request | request | requirement | implementation | test_result | decision | release | risk | data_model | automation | integration | api
tags: [tag1, tag2, tag3]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: ["docs/filename.md", "docs/other.md"]
client: "Cliente"
project: "Progetto"
request_id: "REQ-001"
status: candidate | validated | implemented | tested | released | superseded | conflict
authority: context | client_input | validated_report | test_evidence | deliverable
---
```

### Field Rules

| Field     | Required | Notes                                                       |
|-----------|----------|-------------------------------------------------------------|
| `title`   | yes      | Human-readable, title case                                  |
| `type`    | yes      | One of the supported page types below                       |
| `tags`    | yes      | At least one tag; lowercase with hyphens                    |
| `created` | yes      | ISO date of first creation                                  |
| `updated` | yes      | ISO date of last modification — update on every edit        |
| `sources` | yes      | List of docs/ files this page draws from; empty list `[]` if none |

---

## Page Types

### `entity`
A named real-world thing: person, organization, product, place.
- File location: `wiki/entities/Name_Of_Entity.md`
- Contains: description, key facts, relationships, timeline
- Example: `wiki/entities/OpenAI.md`, `wiki/entities/Sam_Altman.md`

### `concept`
An idea, technique, algorithm, or pattern.
- File location: `wiki/concepts/ConceptName.md`
- Contains: definition, how it works, use cases, trade-offs
- Example: `wiki/concepts/Retrieval_Augmented_Generation.md`

### `summary`
A digest of a single source document.
- File location: `wiki/summaries/SourceFileName.md`
- Contains: key points, main arguments, notable quotes (with attribution)
- Example: `wiki/summaries/attention_is_all_you_need.md`

### `comparison`
Side-by-side analysis of two or more entities or concepts.
- File location: `wiki/comparisons/A_vs_B.md`
- Contains: comparison table, pros/cons, when to use which
- Example: `wiki/comparisons/GPT4_vs_Claude.md`

### `overview`
A landscape view of a topic area, linking to many other pages.
- File location: `wiki/overviews/TopicArea.md`
- Contains: taxonomy, key players, key concepts, recommended reading order
- Example: `wiki/overviews/Large_Language_Models.md`

### `analysis`
A reasoned argument, opinion synthesis, or inference drawn from sources.
- File location: `wiki/analysis/TopicAnalysis.md`
- Contains: thesis, evidence (with citations), conclusion, open questions
- Example: `wiki/analysis/Scaling_Laws_Implications.md`

### Project delivery types
Use these page types for consulting-project knowledge:
- `meeting_note`: transcript/sintesi meeting e contesto NotebookLM; authority `context`.
- `client_source`: documento fornito dal cliente; authority `client_input`.
- `candidate_request`: richiesta emersa ma non ancora validata.
- `request`: richiesta validata end-to-end da development report.
- `requirement`: requisito funzionale/non funzionale collegato a una request.
- `implementation`: sintesi tecnica validata.
- `test_result`: evidenza test e validazione.
- `decision`: decisione tecnica o funzionale.
- `release`: changelog/rilascio.
- `risk`: rischio, gap o conflitto tra fonti.
- `data_model`, `automation`, `integration`, `api`: dettagli specialistici.

---

## Cross-Reference Format

Use `[[Page Name]]` for wiki-internal links. The page name matches the `title` field.

```markdown
See also [[Retrieval Augmented Generation]] and [[OpenAI]].
```

Standard markdown links for external URLs:
```markdown
[Attention Is All You Need](https://arxiv.org/abs/1706.03762)
```

---

## Ingest Workflow

Use `wiki_assist` as the primary entry point:

1. **Setup**: `wiki_assist goal="inizializza wiki" apply=true`.
2. **Development thread**: synthesize the thread into `thread_report`, then call `wiki_assist goal="aggiorna wiki" thread_report="..." apply=true`.
3. **Client source / transcript**: call `wiki_assist goal="aggiorna wiki da documento" category="client|transcripts" path="..." source_kind="..." apply=true`.
4. **Health**: call `wiki_assist goal="controlla stato wiki"`.

Granular tools such as `wiki_normalize_source`, `wiki_prepare_source_ingestion`, `wiki_write_page`, `wiki_rebuild_index` and `wiki_append_log` are advanced/debug tools.

---

## Query Workflow

When answering a question using the wiki:

1. **Search first**: Use `wiki_search` with key terms from the question.
2. **Read top results**: Use `wiki_read_page` on the most relevant results.
3. **Follow links**: If a page references `[[Other Page]]`, read that too if relevant.
4. **Check index**: If search returns nothing, use `wiki_read_index` to browse by category.
5. **Synthesize**: Combine information from multiple pages, noting the `sources` field for provenance.
6. **Do not hallucinate**: If the wiki lacks the information, say so clearly and suggest ingesting relevant sources.

---

## Lint Checklist

Run `wiki_lint` periodically and fix:

- **Orphan pages**: Pages with no inbound `[[links]]` — connect them to an overview or the index.
- **Missing pages**: `[[links]]` referencing non-existent pages — create the page or remove the link.
- **Broken markdown links**: Fix or remove.
- **Stale `updated` fields**: If you edited a page, ensure `updated:` reflects today's date.
- **Empty `sources`**: Every summary page must have at least one source.

---

## Naming Conventions

| Item          | Convention                         | Example                          |
|---------------|------------------------------------|----------------------------------|
| Entity pages  | Title_Case_With_Underscores.md     | `Sam_Altman.md`               |
| Concept pages | Descriptive_Name.md                | `Chain_of_Thought.md`         |
| Summary pages | Match source filename (lowercased) | `attention_is_all_you_need.md`|
| Tags          | lowercase-with-hyphens             | `large-language-model`        |
| WikiLinks     | Match the `title` field          | `[[Sam Altman]]`             |

---

---

## Document Generation Workflow

Usa questo workflow editoriale per produrre documenti strutturati (spec funzionali, architetture, ecc.) dalla conoscenza accumulata nella wiki senza perdere contenuti in contesti lunghi:

1. **Pianifica come redattore**: Chiama `wiki_plan_document` con `document_type`, opzionalmente `project_name`, `objective` e `audience`. Il redattore definisce sezioni, checklist, stile e strategia di copertura.
2. **Prepara context pack mirati**: Per ogni sezione, chiama `wiki_get_section_context` con `section_title`, query mirata, eventuali `page_paths`, filtri `page_types` e budget di caratteri.
3. **Verifica codice quando la wiki non basta**: Se una sezione è poco chiara o incompleta, chiama `wiki_get_code_context` con query specifiche su flussi, API, configurazioni, modelli dati o componenti. Il codice serve per aggiornare la wiki, non per esporre percorsi interni nel documento cliente.
4. **Aggiorna la wiki prima del documento**: Per lacune o inesattezze, chiama `wiki_prepare_knowledge_updates`, applica la bozza con `wiki_write_page`, poi `wiki_update_index` e `wiki_append_log`. Dopo l'aggiornamento, rigenera il context pack della sezione.
5. **Assegna i writer**: Ogni writer scrive una sezione usando solo il proprio context pack aggiornato. Deve segnalare lacune invece di inventare, mantenere italiano professionale e rimuovere ogni placeholder.
6. **Assembla come redattore**: Unisci le sezioni in un documento coerente, elimina duplicazioni, uniforma terminologia e tono. Inserisci diagrammi `mermaid` solo quando chiariscono flussi, architetture, dati o sequenze; non usare ASCII art.
7. **Salva la bozza**: Chiama `wiki_write_document` con `filename`, `title`, `document_type` e il `content` completo. Usa un nome file con versione (es. `documento_funzionale_v1.md`).
8. **Revisiona**: Chiama `wiki_review_document` sul file salvato con `client_facing=true`, `language="italiano"` e `include_wiki_update_plan=true`. Risolvi finding, placeholder, sezioni mancanti/deboli, problemi linguistici, riferimenti interni e problemi Mermaid.
9. **Recupera lacune post-review**: Se la review produce `Piano aggiornamento wiki`, esegui le azioni indicate: `wiki_search`, `wiki_read_page`, `wiki_get_code_context`, `wiki_prepare_knowledge_updates`, `wiki_write_page`, `wiki_update_index`, `wiki_append_log`. Poi aggiorna il documento.
10. **Verifica e registra**: Chiama `wiki_list_files` sulla categoria `deliverables`, `wiki_read_file` se serve controllare il contenuto, e aggiungi una entry con `wiki_append_log` indicando cosa è stato generato, revisionato e aggiornato nella wiki.

### Tipi di documento

| Tipo | Descrizione | Persona adottata |
|------|-------------|-----------------|
| `functional_spec` | Documento Funzionale di Progetto completo in italiano | PM esperto |
| `architecture_doc` | Architettura di sistema e decisioni tecniche | Solution Architect / Tech Lead |
| `project_brief` | Sintesi esecutiva per stakeholder | Business Analyst |
| `onboarding_guide` | Guida onboarding per nuovi sviluppatori | Senior Developer |
| `api_reference` | Documentazione endpoint e interfacce API | Backend Developer / API Specialist |
| `custom` | Qualsiasi altro tipo (nessun template predefinito) | — |

### Storage

I documenti vengono salvati in `docs/deliverables/`. Non sono pagine wiki e **non richiedono frontmatter**.

---

### Regole qualità documenti

- Scrivere sempre in italiano professionale, pulito e concreto.
- Non lasciare placeholder come `[Descrivere...]`, `[Nome]` o `{{PROJECT_NAME}}` nel documento finale.
- Non inventare dettagli non presenti nella wiki: dichiarare lacune, assunzioni o dati da confermare.
- Il documento finale è sempre destinato a un cliente: non citare wiki, context pack, agent, prompt, tool MCP, percorsi `src/`, `tests/`, `docs/` o dettagli del processo interno.
- Quando la wiki è insufficiente ma il codice chiarisce il funzionamento, aggiornare prima la wiki con una pagina o sezione verificata e poi rigenerare il documento.
- Usare tabelle e criteri verificabili quando aiutano la validazione.
- Usare blocchi Markdown ```mermaid solo quando il diagramma aggiunge chiarezza; non usare diagrammi ASCII o alberi monospaziati.

*Schema version 1.3 — Update this file when conventions evolve.*
