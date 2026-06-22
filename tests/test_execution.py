from __future__ import annotations

from pathlib import Path
import json

import pytest

from salesforce_mcp.config import Settings
from salesforce_mcp.execution import ExecutionEngine
from salesforce_mcp.journal import JournalStore


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        org_url=None,
        instance_url=None,
        access_token=None,
        api_version="61.0",
        datacloud_query_url=None,
        datacloud_api_url=None,
        datacloud_ingestion_url=None,
        datacloud_access_token=None,
        oauth_client_id=None,
        oauth_client_secret=None,
        oauth_redirect_uri="http://localhost:1717/oauth/callback",
        oauth_scopes="api refresh_token",
        profile="test",
        headless=True,
        timeout_ms=1000,
        viewport_width=800,
        viewport_height=600,
        auth_dir=tmp_path / ".auth",
        logs_dir=tmp_path / "logs",
        runs_dir=tmp_path / "runs",
        journal_redact_fields=("token", "password"),
    )


def test_plan_request_creates_data_stream_journal(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    run = engine.plan_request(
        request='{"stream":{"name":"Customers"},"verification":{"salesforce_soql":"SELECT Id FROM Account"}}',
        target_area="data_streams",
        dry_run=True,
    )

    assert run["run_id"].startswith("run_")
    assert run["workflow"] == "configure_data_stream"
    assert run["dry_run"] is True
    assert [step["id"] for step in run["steps"]] == [
        "precheck_session",
        "capture_before_state",
        "before_salesforce_query",
        "dry_run_review",
        "after_salesforce_query",
        "final_recommendation",
    ]


def test_list_capabilities_includes_datacloud_workflows(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))

    capabilities = engine.list_capabilities()["capabilities"]

    names = {capability["name"] for capability in capabilities}  # type: ignore[index]
    assert {
        "configure_data_stream",
        "ingest_streaming_records",
        "ingest_bulk_csv",
        "inspect_data_model",
        "validate_identity_resolution",
        "validate_calculated_insight",
        "validate_data_action",
    }.issubset(names)


def test_plan_request_supports_metadata_validation_workflow(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    run = engine.plan_request(
        request='{"metadata":{"entity_type":"DataModelObject","entity_name":"UnifiedIndividual__dlm"}}',
        target_area="inspect_data_model",
        dry_run=True,
    )

    assert run["workflow"] == "inspect_data_model"
    assert [step["type"] for step in run["steps"]] == ["datacloud_metadata", "recommendation"]


def test_streaming_ingestion_requires_approval_when_not_dry_run(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    run = engine.plan_request(
        request='{"ingestion":{"connector_name":"crm","object_name":"Contact","records":[{"Id":"1"}]}}',
        target_area="ingest_streaming_records",
        dry_run=False,
    )

    ingest_step = next(step for step in run["steps"] if step["id"] == "ingest_streaming_records")
    assert ingest_step["requires_approval"] is True
    assert ingest_step["input"]["risk"] == "write"


def test_bulk_ingestion_plan_includes_upload_close_and_status(tmp_path: Path) -> None:
    csv_path = tmp_path / "contacts.csv"
    csv_path.write_text("Id,Name\n1,Ada\n", encoding="utf-8")
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    request = json.dumps(
        {"ingestion": {"connector_name": "crm", "object_name": "Contact", "csv_path": str(csv_path)}}
    )

    run = engine.plan_request(
        request=request,
        target_area="ingest_bulk_csv",
        dry_run=False,
    )

    assert [step["id"] for step in run["steps"]] == [
        "validate_bulk_csv",
        "create_bulk_job",
        "upload_bulk_csv",
        "close_bulk_job",
        "bulk_job_status",
        "final_recommendation",
    ]
    assert run["steps"][1]["requires_approval"] is True


def test_journal_redacts_configured_fields(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    run = engine.plan_request(
        request='{"ingestion":{"connector_name":"crm","object_name":"Contact","records":[{"access_token":"secret"}]}}',
        target_area="ingest_streaming_records",
        dry_run=True,
    )

    raw = json.loads((tmp_path / "runs" / str(run["run_id"]) / "run.json").read_text(encoding="utf-8"))
    assert raw["steps"][0]["input"]["records"][0]["access_token"] == "***REDACTED***"


def test_approve_step_marks_supervised_step(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    run = engine.plan_request(request="configure stream", target_area="data_streams", dry_run=False)

    approved = engine.approve_step(str(run["run_id"]), "configure_data_stream")
    configure_step = next(step for step in approved["steps"] if step["id"] == "configure_data_stream")

    assert configure_step["approved"] is True
    assert configure_step["status"] == "approved"


@pytest.mark.anyio
async def test_rollback_safe_without_resources_goes_to_manual_review(tmp_path: Path) -> None:
    engine = ExecutionEngine(JournalStore(_settings(tmp_path)))
    run = engine.plan_request(request="configure stream", target_area="data_streams", dry_run=True)

    rolled_back = await engine.rollback_run(str(run["run_id"]), mode="safe")

    assert rolled_back["status"] == "needs_review"
    assert rolled_back["recommendation"] == "human_review"
    assert rolled_back["steps"][-1]["type"] == "rollback"
