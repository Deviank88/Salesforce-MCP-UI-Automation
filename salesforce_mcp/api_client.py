from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .auth import runtime_tokens
from .config import Settings, load_settings


@dataclass
class ApiResult:
    ok: bool
    configured: bool
    status_code: int | None
    data: Any = None
    error: str | None = None
    headers: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "configured": self.configured,
            "status_code": self.status_code,
            "data": self.data,
            "error": self.error,
            "headers": self.headers or {},
        }


class SalesforceApiClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()

    def query_salesforce(self, soql: str) -> dict[str, object]:
        instance_url, access_token = self._salesforce_credentials()
        if not instance_url or not access_token:
            return ApiResult(
                ok=False,
                configured=False,
                status_code=None,
                error=(
                    "Set SALESFORCE_INSTANCE_URL and SALESFORCE_ACCESS_TOKEN, or call "
                    "use_browser_session_token/start_oauth_token_flow first."
                ),
            ).to_dict()

        path = f"/services/data/v{self.settings.api_version}/query"
        url = instance_url.rstrip("/") + path + "?" + urlencode({"q": soql})
        return self._json_request("GET", url, access_token).to_dict()

    def query_datacloud(self, sql_or_query: str) -> dict[str, object]:
        if self.settings.datacloud_query_url:
            return self._datacloud_json_request(
                "POST",
                self.settings.datacloud_query_url,
                {"query": sql_or_query, "sql": sql_or_query},
                absolute_url=True,
            )
        return self.datacloud_submit_query(sql_or_query, mode="ADAPTIVE")

    def datacloud_submit_query(self, sql: str, mode: str = "ADAPTIVE") -> dict[str, object]:
        return self._datacloud_json_request(
            "POST",
            "/api/v3/query",
            {"sql": sql, "query": sql, "mode": mode.upper()},
        )

    def datacloud_query_status(self, query_id: str) -> dict[str, object]:
        return self._datacloud_json_request("GET", f"/api/v3/query/{query_id}")

    def datacloud_query_rows(self, query_id: str, offset: int = 0, row_limit: int = 1000) -> dict[str, object]:
        query = urlencode({"offset": max(offset, 0), "rowLimit": max(1, min(row_limit, 50000))})
        return self._datacloud_json_request("GET", f"/api/v3/query/{query_id}/rows?{query}")

    def datacloud_cancel_query(self, query_id: str) -> dict[str, object]:
        return self._datacloud_json_request("DELETE", f"/api/v3/query/{query_id}")

    def datacloud_metadata(
        self,
        entity_type: str | None = None,
        entity_category: str | None = None,
        entity_name: str | None = None,
    ) -> dict[str, object]:
        params = {
            key: value
            for key, value in {
                "entityType": entity_type,
                "entityCategory": entity_category,
                "entityName": entity_name,
            }.items()
            if value
        }
        path = "/api/v1/metadata/" + (("?" + urlencode(params)) if params else "")
        return self._datacloud_json_request("GET", path)

    def datacloud_validate_streaming_records(
        self,
        connector_name: str,
        object_name: str,
        records: list[dict[str, Any]],
    ) -> dict[str, object]:
        path = f"/api/v1/ingest/sources/{connector_name}/{object_name}/actions/test"
        return self._datacloud_json_request("POST", path, {"data": records}, service="ingestion")

    def datacloud_ingest_streaming_records(
        self,
        connector_name: str,
        object_name: str,
        records: list[dict[str, Any]],
    ) -> dict[str, object]:
        path = f"/api/v1/ingest/sources/{connector_name}/{object_name}"
        return self._datacloud_json_request("POST", path, {"data": records}, service="ingestion")

    def datacloud_create_bulk_job(
        self,
        connector_name: str,
        object_name: str,
        operation: str = "upsert",
    ) -> dict[str, object]:
        payload = {"sourceName": connector_name, "objectName": object_name, "operation": operation}
        return self._datacloud_json_request("POST", "/api/v1/ingest/jobs", payload, service="ingestion")

    def datacloud_bulk_job_status(self, job_id: str) -> dict[str, object]:
        return self._datacloud_json_request("GET", f"/api/v1/ingest/jobs/{job_id}", service="ingestion")

    def datacloud_upload_bulk_csv(self, job_id: str, csv_text: str) -> dict[str, object]:
        return self._datacloud_raw_request(
            "PUT",
            f"/api/v1/ingest/jobs/{job_id}/batches",
            csv_text.encode("utf-8"),
            "text/csv",
            service="ingestion",
        )

    def datacloud_close_bulk_job(self, job_id: str) -> dict[str, object]:
        return self._datacloud_json_request(
            "PATCH",
            f"/api/v1/ingest/jobs/{job_id}",
            {"state": "UploadComplete"},
            service="ingestion",
        )

    def _datacloud_json_request(
        self,
        method: str,
        path_or_url: str,
        payload: dict[str, Any] | None = None,
        *,
        service: str = "query",
        absolute_url: bool = False,
        retries: int = 1,
    ) -> dict[str, object]:
        base_url = self._datacloud_base_url(service)
        token = self._datacloud_access_token()
        if not token or (not absolute_url and not base_url):
            env_name = "SALESFORCE_DATACLOUD_INGESTION_URL" if service == "ingestion" else "SALESFORCE_DATACLOUD_API_URL"
            return ApiResult(
                ok=False,
                configured=False,
                status_code=None,
                error=(
                    f"Set {env_name} and SALESFORCE_DATACLOUD_ACCESS_TOKEN, or call "
                    f"start_oauth_token_flow first, to enable Data Cloud {service} API calls."
                ),
            ).to_dict()

        url = path_or_url if absolute_url else self._join_url(str(base_url), path_or_url)
        for attempt in range(max(1, retries + 1)):
            result = self._json_request(method, url, token, payload=payload)
            if result.status_code != 429 or attempt >= retries:
                return result.to_dict()
            time.sleep(min(2**attempt, 8))
        return result.to_dict()

    def _datacloud_raw_request(
        self,
        method: str,
        path: str,
        body: bytes,
        content_type: str,
        *,
        service: str,
    ) -> dict[str, object]:
        base_url = self._datacloud_base_url(service)
        token = self._datacloud_access_token()
        if not token or not base_url:
            return ApiResult(
                ok=False,
                configured=False,
                status_code=None,
                error=(
                    f"Set SALESFORCE_DATACLOUD_INGESTION_URL and SALESFORCE_DATACLOUD_ACCESS_TOKEN, or call "
                    f"start_oauth_token_flow first, to enable Data Cloud {service} API calls."
                ),
            ).to_dict()
        return self._request(
            method,
            self._join_url(base_url, path),
            token,
            body=body,
            content_type=content_type,
        ).to_dict()

    def _datacloud_base_url(self, service: str) -> str | None:
        if service == "ingestion":
            return self.settings.datacloud_ingestion_url or self.settings.datacloud_api_url
        return self.settings.datacloud_api_url

    def _join_url(self, base_url: str, path: str) -> str:
        return base_url.rstrip("/") + "/" + path.lstrip("/")

    def _salesforce_credentials(self) -> tuple[str | None, str | None]:
        token = runtime_tokens.salesforce()
        if token:
            return token.instance_url or self.settings.instance_url, token.access_token
        return self.settings.instance_url, self.settings.access_token

    def _datacloud_access_token(self) -> str | None:
        token = runtime_tokens.datacloud()
        return token.access_token if token else self.settings.datacloud_access_token

    def _json_request(self, method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> ApiResult:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        return self._request(method, url, token, body=body, content_type="application/json")

    def _request(
        self,
        method: str,
        url: str,
        token: str,
        body: bytes | None = None,
        content_type: str = "application/json",
    ) -> ApiResult:
        request = Request(
            url=url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": content_type,
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
                headers = {key.lower(): value for key, value in response.getheaders()}
                return ApiResult(ok=True, configured=True, status_code=response.status, data=data, headers=headers)
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return ApiResult(ok=False, configured=True, status_code=exc.code, error=raw or str(exc))
        except (URLError, TimeoutError) as exc:
            return ApiResult(ok=False, configured=True, status_code=None, error=str(exc))


api_client = SalesforceApiClient()
