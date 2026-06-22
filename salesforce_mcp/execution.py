from __future__ import annotations

from pathlib import Path
from typing import Any

from .api_client import api_client
from .assertions import assert_records
from .browser import browser
from .guardrails import guard_dangerous_action
from .journal import JournalStore, RunJournal, RunStep, store, utc_now
from .workflows import build_plan, list_capabilities


class ExecutionEngine:
    def __init__(self, journal_store: JournalStore | None = None) -> None:
        self.store = journal_store or store

    def plan_request(self, request: str, target_area: str = "data_streams", dry_run: bool = True) -> dict[str, object]:
        journal = build_plan(request=request, target_area=target_area, dry_run=dry_run)
        self.store.create(journal)
        return journal.to_dict()

    def list_capabilities(self) -> dict[str, object]:
        return list_capabilities()

    def get_run_status(self, run_id: str) -> dict[str, object]:
        return self.store.load(run_id).to_dict()

    def approve_step(self, run_id: str, step_id: str) -> dict[str, object]:
        return self.store.approve_step(run_id, step_id).to_dict()

    async def execute_plan(self, run_id: str, max_attempts: int = 3) -> dict[str, object]:
        journal = self.store.load(run_id)
        journal.max_attempts = max(1, min(max_attempts, 5))
        journal.status = "running"
        self.store.save(journal)

        for step in journal.steps:
            if step.status in {"succeeded", "skipped"}:
                continue
            if step.requires_approval and not step.approved:
                step.status = "awaiting_approval"
                step.updated_at = utc_now()
                journal.status = "awaiting_approval"
                journal.recommendation = "human_review"
                self.store.save(journal)
                return journal.to_dict()

            await self._run_step(journal, step)
            self.store.save(journal)
            if step.status == "failed":
                journal.status = "failed"
                journal.recommendation = "retry" if step.attempts < journal.max_attempts else "human_review"
                self.store.save(journal)
                return journal.to_dict()

        journal.status = "succeeded"
        journal.recommendation = self._final_recommendation(journal)
        return self.store.save(journal).to_dict()

    async def rollback_run(
        self,
        run_id: str,
        mode: str = "safe",
        confirm_dangerous: bool = False,
    ) -> dict[str, object]:
        journal = self.store.load(run_id)
        mode = mode.strip().lower()
        if mode not in {"safe", "manual_review", "dangerous"}:
            raise ValueError("mode must be one of safe, manual_review, dangerous.")
        if mode == "dangerous":
            guard_dangerous_action(confirm_dangerous, "dangerous rollback")

        managed_resources = [
            resource
            for resource in journal.resources
            if resource.get("created_by_run") is True or resource.get("managed") is True
        ]
        rollback_step = RunStep(
            id=f"rollback_{len(journal.steps) + 1}",
            type="rollback",
            description=f"Rollback {mode} delle risorse tracciate nel run.",
            input={"mode": mode, "managed_resources": managed_resources},
        )

        if mode == "manual_review" or not managed_resources:
            rollback_step.status = "succeeded"
            rollback_step.output = {
                "message": "No automatic cleanup executed. Review the tracked resources and screenshots manually.",
                "managed_resources": managed_resources,
            }
            journal.status = "needs_review"
            journal.recommendation = "human_review"
        else:
            rollback_step.status = "awaiting_approval" if mode == "safe" else "succeeded"
            rollback_step.output = {
                "message": (
                    "Safe rollback is prepared but no Salesforce-specific delete/deactivate implementation "
                    "is enabled in this MVP."
                ),
                "managed_resources": managed_resources,
            }
            journal.status = "needs_review"
            journal.recommendation = "human_review"

        rollback_step.updated_at = utc_now()
        journal.steps.append(rollback_step)
        return self.store.save(journal).to_dict()

    async def _run_step(self, journal: RunJournal, step: RunStep) -> None:
        step.status = "running"
        step.attempts += 1
        step.updated_at = utc_now()
        try:
            if step.type == "precheck":
                result = await browser.snapshot(include_screenshot=True)
                step.output = {
                    "snapshot": result,
                    "logged_in": not result.get("warnings"),
                }
            elif step.type == "browser_snapshot":
                step.output = await browser.snapshot(
                    include_screenshot=bool(step.input.get("include_screenshot", True)),
                    include_dom=bool(step.input.get("include_dom", False)),
                )
            elif step.type == "query_salesforce":
                step.output = api_client.query_salesforce(str(step.input["soql"]))
            elif step.type == "query_datacloud":
                step.output = api_client.query_datacloud(str(step.input["query"]))
            elif step.type == "datacloud_metadata":
                step.output = api_client.datacloud_metadata(
                    entity_type=self._optional_str(step.input.get("entity_type")),
                    entity_category=self._optional_str(step.input.get("entity_category")),
                    entity_name=self._optional_str(step.input.get("entity_name")),
                )
            elif step.type == "validate_streaming_records":
                connector_name, object_name = self._connector_and_object(step)
                records = self._records(step)
                step.output = api_client.datacloud_validate_streaming_records(connector_name, object_name, records)
            elif step.type == "ingest_streaming_records":
                connector_name, object_name = self._connector_and_object(step)
                records = self._records(step)
                step.output = api_client.datacloud_ingest_streaming_records(connector_name, object_name, records)
            elif step.type == "validate_bulk_csv":
                connector_name, object_name = self._connector_and_object(step)
                csv_path = self._csv_path(step)
                step.output = {
                    "connector_name": connector_name,
                    "object_name": object_name,
                    "csv_path": str(csv_path),
                    "bytes": csv_path.stat().st_size,
                    "header": csv_path.read_text(encoding="utf-8-sig").splitlines()[0].split(","),
                }
            elif step.type == "create_bulk_job":
                connector_name, object_name = self._connector_and_object(step)
                operation = str(step.input.get("operation") or "upsert")
                step.output = api_client.datacloud_create_bulk_job(connector_name, object_name, operation)
            elif step.type == "upload_bulk_csv":
                job_id = self._last_job_id(journal)
                step.output = api_client.datacloud_upload_bulk_csv(job_id, self._csv_path(step).read_text(encoding="utf-8-sig"))
            elif step.type == "close_bulk_job":
                step.output = api_client.datacloud_close_bulk_job(self._last_job_id(journal))
            elif step.type == "bulk_job_status":
                job_id = self._last_job_id(journal)
                step.output = api_client.datacloud_bulk_job_status(job_id)
            elif step.type == "browser_action":
                result = await browser.open_datacloud_area(str(step.input.get("area", "data streams")))
                step.output = {
                    "message": "Data Streams area opened for supervised configuration.",
                    "snapshot": result,
                }
            elif step.type == "assert_records":
                records = self._last_query_records(journal)
                step.output = assert_records(dict(step.input["assertion"]), records=records)
                if not step.output.get("passed"):
                    raise ValueError("Record assertion failed.")
            elif step.type in {"review", "recommendation"}:
                step.output = {"message": "Step completed.", "recommendation": self._final_recommendation(journal)}
            else:
                raise ValueError(f"Unsupported step type: {step.type}")
            step.status = "succeeded"
        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)
        finally:
            step.updated_at = utc_now()

    def _last_query_records(self, journal: RunJournal) -> list[dict[str, Any]]:
        for step in reversed(journal.steps):
            if step.type not in {"query_salesforce", "query_datacloud"} or not step.output:
                continue
            data = step.output.get("data")
            if isinstance(data, dict):
                records = data.get("records") or data.get("data")
                if isinstance(records, list):
                    return [record for record in records if isinstance(record, dict)]
        return []

    def _optional_str(self, value: object) -> str | None:
        return str(value) if value not in (None, "") else None

    def _connector_and_object(self, step: RunStep) -> tuple[str, str]:
        connector_name = self._optional_str(step.input.get("connector_name"))
        object_name = self._optional_str(step.input.get("object_name"))
        if not connector_name or not object_name:
            raise ValueError("connector_name and object_name are required.")
        return connector_name, object_name

    def _records(self, step: RunStep) -> list[dict[str, Any]]:
        records = step.input.get("records")
        if not isinstance(records, list) or not records or not all(isinstance(record, dict) for record in records):
            raise ValueError("records must be a non-empty list of objects.")
        return records

    def _csv_path(self, step: RunStep) -> Path:
        value = self._optional_str(step.input.get("csv_path"))
        if not value:
            raise ValueError("csv_path is required.")
        path = Path(value)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists() or not path.is_file():
            raise ValueError(f"CSV file not found: {path}")
        if path.suffix.lower() != ".csv":
            raise ValueError("csv_path must point to a .csv file.")
        return path

    def _last_job_id(self, journal: RunJournal) -> str:
        for step in reversed(journal.steps):
            if not step.output:
                continue
            data = step.output.get("data")
            if isinstance(data, dict):
                job_id = data.get("jobId") or data.get("id") or data.get("job_id")
                if job_id:
                    return str(job_id)
        raise ValueError("No bulk job id found in previous step output.")

    def _final_recommendation(self, journal: RunJournal) -> str:
        failed = [step for step in journal.steps if step.status == "failed"]
        awaiting = [step for step in journal.steps if step.status == "awaiting_approval"]
        if awaiting:
            return "human_review"
        if failed:
            return "retry" if any(step.attempts < journal.max_attempts for step in failed) else "human_review"
        if journal.dry_run:
            return "human_review"
        return "keep"

    def compare_before_after(self, run_id: str) -> dict[str, object]:
        journal = self.store.load(run_id)
        before = [step for step in journal.steps if step.id.startswith("before_")]
        after = [step for step in journal.steps if step.id.startswith("after_")]
        return {
            "run_id": run_id,
            "before": [step.output for step in before],
            "after": [step.output for step in after],
            "recommendation": journal.recommendation,
        }


engine = ExecutionEngine()
