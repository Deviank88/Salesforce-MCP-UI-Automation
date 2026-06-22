from __future__ import annotations

from pathlib import Path

from salesforce_mcp.api_client import ApiResult, SalesforceApiClient
from salesforce_mcp.config import Settings


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values = dict(
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
    values.update(overrides)
    return Settings(**values)


class RecordingClient(SalesforceApiClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []

    def _json_request(self, method: str, url: str, token: str, payload: dict[str, object] | None = None) -> ApiResult:
        self.calls.append((method, url, payload))
        return ApiResult(ok=True, configured=True, status_code=200, data={"id": "ok"})


def test_query_salesforce_requires_configuration(tmp_path: Path) -> None:
    client = SalesforceApiClient(_settings(tmp_path))

    result = client.query_salesforce("SELECT Id FROM Account")

    assert result["ok"] is False
    assert result["configured"] is False
    assert "SALESFORCE_INSTANCE_URL" in str(result["error"])


def test_datacloud_query_api_builds_structured_paths(tmp_path: Path) -> None:
    client = RecordingClient(
        _settings(
            tmp_path,
            datacloud_api_url="https://tenant.example.com",
            datacloud_access_token="token",
        )
    )

    client.datacloud_submit_query("SELECT 1", mode="async")
    client.datacloud_query_status("q123")
    client.datacloud_query_rows("q123", offset=10, row_limit=25)
    client.datacloud_cancel_query("q123")

    assert client.calls[0] == (
        "POST",
        "https://tenant.example.com/api/v3/query",
        {"sql": "SELECT 1", "query": "SELECT 1", "mode": "ASYNC"},
    )
    assert client.calls[1][1].endswith("/api/v3/query/q123")
    assert client.calls[2][1].endswith("/api/v3/query/q123/rows?offset=10&rowLimit=25")
    assert client.calls[3][0] == "DELETE"


def test_datacloud_metadata_filters(tmp_path: Path) -> None:
    client = RecordingClient(
        _settings(
            tmp_path,
            datacloud_api_url="https://tenant.example.com/",
            datacloud_access_token="token",
        )
    )

    client.datacloud_metadata(entity_type="DataModelObject", entity_name="UnifiedIndividual__dlm")

    assert client.calls == [
        (
            "GET",
            "https://tenant.example.com/api/v1/metadata/?entityType=DataModelObject&entityName=UnifiedIndividual__dlm",
            None,
        )
    ]


def test_streaming_ingestion_uses_ingestion_base_url(tmp_path: Path) -> None:
    client = RecordingClient(
        _settings(
            tmp_path,
            datacloud_ingestion_url="https://ingest.example.com",
            datacloud_access_token="token",
        )
    )

    client.datacloud_ingest_streaming_records("crm", "Contact", [{"Id": "1"}])

    assert client.calls == [
        (
            "POST",
            "https://ingest.example.com/api/v1/ingest/sources/crm/Contact",
            {"data": [{"Id": "1"}]},
        )
    ]
