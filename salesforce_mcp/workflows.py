from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .journal import RunJournal, RunStep, new_run_id


Builder = Callable[[str, str, bool], RunJournal]


@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    target_area: str
    aliases: tuple[str, ...]
    description: str
    risk: str
    input_fields: tuple[str, ...]
    builder: Builder

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "target_area": self.target_area,
            "aliases": list(self.aliases),
            "description": self.description,
            "risk": self.risk,
            "input_fields": list(self.input_fields),
        }


def parse_request_payload(request: str) -> dict[str, Any]:
    try:
        value = json.loads(request)
    except json.JSONDecodeError:
        return {"description": request}
    return value if isinstance(value, dict) else {"description": request, "value": value}


def _run(request: str, target_area: str, workflow: str, dry_run: bool) -> RunJournal:
    return RunJournal(
        run_id=new_run_id(),
        request=request,
        target_area=target_area,
        workflow=workflow,
        dry_run=dry_run,
        recommendation="human_review",
    )


def _step(
    step_id: str,
    step_type: str,
    description: str,
    input: dict[str, object] | None = None,
    *,
    risk: str = "read",
    approval: bool = False,
) -> RunStep:
    return RunStep(
        id=step_id,
        type=step_type,
        description=description,
        input={**(input or {}), "risk": risk},
        requires_approval=approval,
    )


def _verification_steps(payload: dict[str, Any], phase: str) -> list[RunStep]:
    verification = payload.get("verification", {}) if isinstance(payload.get("verification"), dict) else {}
    steps: list[RunStep] = []
    if verification.get("salesforce_soql"):
        steps.append(
            _step(
                f"{phase}_salesforce_query",
                "query_salesforce",
                f"Esegue SOQL {phase} per baseline o validazione.",
                {"soql": verification["salesforce_soql"]},
            )
        )
    if verification.get("datacloud_query"):
        steps.append(
            _step(
                f"{phase}_datacloud_query",
                "query_datacloud",
                f"Esegue query Data Cloud {phase} per baseline o validazione.",
                {"query": verification["datacloud_query"]},
            )
        )
    return steps


def _assertion_step(payload: dict[str, Any]) -> list[RunStep]:
    verification = payload.get("verification", {}) if isinstance(payload.get("verification"), dict) else {}
    return (
        [
            _step(
                "assert_records",
                "assert_records",
                "Valida record e criteri di successo dichiarati.",
                {"assertion": verification["assertion"]},
            )
        ]
        if verification.get("assertion")
        else []
    )


def build_data_stream_plan(request: str, target_area: str, dry_run: bool) -> RunJournal:
    payload = parse_request_payload(request)
    run = _run(request, target_area, "configure_data_stream", dry_run)
    stream = payload.get("stream", {}) if isinstance(payload.get("stream"), dict) else {}
    verification = payload.get("verification", {}) if isinstance(payload.get("verification"), dict) else {}
    cleanup = payload.get("cleanup", {}) if isinstance(payload.get("cleanup"), dict) else {}

    run.steps.extend(
        [
            _step("precheck_session", "precheck", "Verifica sessione Salesforce, pagina corrente e stato login."),
            _step(
                "capture_before_state",
                "browser_snapshot",
                "Raccoglie snapshot prima della configurazione.",
                {"include_dom": True, "include_screenshot": True},
                risk="ui_only",
            ),
            *_verification_steps(payload, "before"),
        ]
    )
    run.steps.append(
        _step(
            "dry_run_review" if dry_run else "configure_data_stream",
            "review" if dry_run else "browser_action",
            "Conferma piano simulato." if dry_run else "Apre Data Streams e prepara la configurazione supervisionata.",
            {"area": "data streams", "stream": stream, "verification": verification, "cleanup": cleanup},
            risk="ui_only",
            approval=not dry_run,
        )
    )
    run.steps.extend([*_verification_steps(payload, "after"), *_assertion_step(payload)])
    run.steps.append(_step("final_recommendation", "recommendation", "Produce raccomandazione finale."))
    return run


def build_metadata_validation_plan(request: str, target_area: str, dry_run: bool) -> RunJournal:
    payload = parse_request_payload(request)
    run = _run(request, target_area, target_area, dry_run)
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
    query = payload.get("query") or payload.get("datacloud_query")

    run.steps.append(
        _step(
            "datacloud_metadata",
            "datacloud_metadata",
            "Recupera metadata Data Cloud per oggetti, campi, chiavi e relazioni.",
            {
                "entity_type": metadata.get("entity_type"),
                "entity_category": metadata.get("entity_category"),
                "entity_name": metadata.get("entity_name"),
            },
        )
    )
    if query:
        run.steps.append(_step("datacloud_query", "query_datacloud", "Esegue query Data Cloud di validazione.", {"query": query}))
    run.steps.extend(_assertion_step(payload))
    run.steps.append(_step("final_recommendation", "recommendation", "Produce raccomandazione finale."))
    return run


def build_streaming_ingestion_plan(request: str, target_area: str, dry_run: bool) -> RunJournal:
    payload = parse_request_payload(request)
    run = _run(request, target_area, "ingest_streaming_records", dry_run)
    ingestion = payload.get("ingestion", {}) if isinstance(payload.get("ingestion"), dict) else {}
    base = {
        "connector_name": ingestion.get("connector_name"),
        "object_name": ingestion.get("object_name"),
        "records": ingestion.get("records", []),
    }
    run.steps.append(
        _step("validate_streaming_records", "validate_streaming_records", "Valida payload streaming ingestion.", base)
    )
    if not dry_run:
        run.steps.append(
            _step(
                "ingest_streaming_records",
                "ingest_streaming_records",
                "Invia record tramite Streaming Ingestion API.",
                base,
                risk="write",
                approval=True,
            )
        )
    run.steps.extend([*_verification_steps(payload, "after"), *_assertion_step(payload)])
    run.steps.append(_step("final_recommendation", "recommendation", "Produce raccomandazione finale."))
    return run


def build_bulk_ingestion_plan(request: str, target_area: str, dry_run: bool) -> RunJournal:
    payload = parse_request_payload(request)
    run = _run(request, target_area, "ingest_bulk_csv", dry_run)
    ingestion = payload.get("ingestion", {}) if isinstance(payload.get("ingestion"), dict) else {}
    base = {
        "connector_name": ingestion.get("connector_name"),
        "object_name": ingestion.get("object_name"),
        "operation": ingestion.get("operation", "upsert"),
        "csv_path": ingestion.get("csv_path"),
    }
    run.steps.append(_step("validate_bulk_csv", "validate_bulk_csv", "Valida metadata del CSV bulk ingestion.", base))
    if not dry_run:
        run.steps.append(
            _step(
                "create_bulk_job",
                "create_bulk_job",
                "Crea job bulk ingestion supervisionato.",
                base,
                risk="write",
                approval=True,
            )
        )
        run.steps.append(_step("upload_bulk_csv", "upload_bulk_csv", "Carica CSV nel job bulk ingestion.", base, risk="write"))
        run.steps.append(_step("close_bulk_job", "close_bulk_job", "Chiude il job bulk ingestion per l'elaborazione.", {}, risk="write"))
        run.steps.append(_step("bulk_job_status", "bulk_job_status", "Recupera stato del job bulk ingestion.", {}, risk="write"))
    run.steps.extend([*_verification_steps(payload, "after"), *_assertion_step(payload)])
    run.steps.append(_step("final_recommendation", "recommendation", "Produce raccomandazione finale."))
    return run


WORKFLOWS = [
    WorkflowDefinition(
        "configure_data_stream",
        "data_streams",
        ("data_streams", "data streams", "data cloud data streams", "configure_data_stream"),
        "Apre Data Streams e guida configurazione supervisionata via browser.",
        "ui_only",
        ("stream", "verification", "cleanup"),
        build_data_stream_plan,
    ),
    WorkflowDefinition(
        "validate_data_stream",
        "validate_data_stream",
        ("validate_data_stream", "data_stream_validation"),
        "Valida metadata e query collegate a uno stream.",
        "read",
        ("metadata", "query", "verification"),
        build_metadata_validation_plan,
    ),
    WorkflowDefinition(
        "ingest_streaming_records",
        "ingest_streaming_records",
        ("ingest_streaming_records", "streaming_ingestion"),
        "Valida e invia piccoli payload JSON tramite Streaming Ingestion API.",
        "write",
        ("ingestion.connector_name", "ingestion.object_name", "ingestion.records", "verification"),
        build_streaming_ingestion_plan,
    ),
    WorkflowDefinition(
        "ingest_bulk_csv",
        "ingest_bulk_csv",
        ("ingest_bulk_csv", "bulk_ingestion"),
        "Valida e avvia un job Bulk Ingestion API per CSV.",
        "write",
        ("ingestion.connector_name", "ingestion.object_name", "ingestion.csv_path", "verification"),
        build_bulk_ingestion_plan,
    ),
    WorkflowDefinition(
        "inspect_data_model",
        "inspect_data_model",
        ("inspect_data_model", "data_model"),
        "Ispeziona DLO, DMO, relazioni, primary key e key qualifier.",
        "read",
        ("metadata",),
        build_metadata_validation_plan,
    ),
    WorkflowDefinition(
        "validate_identity_resolution",
        "validate_identity_resolution",
        ("validate_identity_resolution", "identity_resolution"),
        "Valida output e profili collegati a identity resolution.",
        "read",
        ("metadata", "query", "verification"),
        build_metadata_validation_plan,
    ),
    WorkflowDefinition(
        "validate_calculated_insight",
        "validate_calculated_insight",
        ("validate_calculated_insight", "calculated_insight", "calculated_insights"),
        "Valida metadata e risultati di una Calculated Insight.",
        "read",
        ("metadata", "query", "verification"),
        build_metadata_validation_plan,
    ),
    WorkflowDefinition(
        "validate_data_action",
        "validate_data_action",
        ("validate_data_action", "data_action", "data_actions"),
        "Valida metadata e dati usati da Data Actions.",
        "read",
        ("metadata", "query", "verification"),
        build_metadata_validation_plan,
    ),
]

WORKFLOW_BY_ALIAS = {alias: workflow for workflow in WORKFLOWS for alias in workflow.aliases}


def list_capabilities() -> dict[str, object]:
    return {"capabilities": [workflow.to_dict() for workflow in WORKFLOWS]}


def build_plan(request: str, target_area: str, dry_run: bool) -> RunJournal:
    workflow = WORKFLOW_BY_ALIAS.get(target_area.strip().lower())
    if workflow is None:
        supported = ", ".join(sorted(WORKFLOW_BY_ALIAS))
        raise ValueError(f"Unsupported target_area: {target_area}. Supported values: {supported}.")
    return workflow.builder(request, workflow.target_area, dry_run)
