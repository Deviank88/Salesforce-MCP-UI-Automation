from __future__ import annotations

from pathlib import Path

from salesforce_mcp.api_client import ApiResult, SalesforceApiClient
from salesforce_mcp.auth import (
    BrowserAuthBridge,
    RuntimeTokenStore,
    TokenBundle,
    create_code_challenge,
    create_code_verifier,
)
from salesforce_mcp.config import Settings


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values = dict(
        org_url="https://example.my.salesforce.com",
        instance_url="https://example.my.salesforce.com",
        access_token=None,
        api_version="61.0",
        datacloud_query_url=None,
        datacloud_api_url=None,
        datacloud_ingestion_url=None,
        datacloud_access_token=None,
        oauth_client_id="client-id",
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
        self.calls: list[tuple[str, str, str]] = []

    def _json_request(self, method: str, url: str, token: str, payload: dict[str, object] | None = None) -> ApiResult:
        self.calls.append((method, url, token))
        return ApiResult(ok=True, configured=True, status_code=200, data={"records": []})


def test_pkce_verifier_and_challenge_are_safe() -> None:
    verifier = create_code_verifier()
    challenge = create_code_challenge(verifier)

    assert 43 <= len(verifier) <= 128
    assert len(challenge) == 43
    assert "=" not in challenge


def test_find_sid_cookie_prefers_matching_salesforce_domain(tmp_path: Path) -> None:
    bridge = BrowserAuthBridge(_settings(tmp_path), RuntimeTokenStore())
    cookies = [
        {"name": "sid", "value": "wrong", "domain": ".other.salesforce.com"},
        {"name": "sid", "value": "right", "domain": ".example.my.salesforce.com"},
    ]

    cookie = bridge.find_sid_cookie(cookies, "https://example.my.salesforce.com/lightning/setup")

    assert cookie is not None
    assert cookie["value"] == "right"


def test_oauth_authorize_url_contains_pkce_parameters(tmp_path: Path) -> None:
    bridge = BrowserAuthBridge(_settings(tmp_path), RuntimeTokenStore())
    url = bridge._authorize_url("verifier", "state-123")

    assert url.startswith("https://example.my.salesforce.com/services/oauth2/authorize?")
    assert "client_id=client-id" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A1717%2Foauth%2Fcallback" in url
    assert "scope=api%20refresh_token" in url
    assert "code_challenge_method=S256" in url


def test_oauth_code_exchange_sends_verifier(tmp_path: Path) -> None:
    class Bridge(BrowserAuthBridge):
        def __init__(self, settings: Settings) -> None:
            super().__init__(settings, RuntimeTokenStore())
            self.payload: dict[str, str | None] = {}

        def _token_request(self, payload: dict[str, str | None]) -> dict[str, object]:
            self.payload = payload
            return {"ok": True, "configured": True, "data": {"access_token": "token"}}

    bridge = Bridge(_settings(tmp_path))

    bridge.exchange_oauth_code("code-123", "verifier-123")

    assert bridge.payload["grant_type"] == "authorization_code"
    assert bridge.payload["code"] == "code-123"
    assert bridge.payload["code_verifier"] == "verifier-123"


def test_token_masking_does_not_expose_values() -> None:
    masked = TokenBundle(access_token="access-secret", refresh_token="refresh-secret").masked()

    assert "access-secret" not in str(masked)
    assert "refresh-secret" not in str(masked)
    assert masked["access_token"] == "***REDACTED***"
    assert masked["refresh_token"] == "***REDACTED***"


def test_api_client_prefers_runtime_salesforce_token(tmp_path: Path) -> None:
    store = RuntimeTokenStore()
    store.set_salesforce(TokenBundle(access_token="runtime-token", instance_url="https://runtime.my.salesforce.com"))
    import salesforce_mcp.api_client as api_client_module

    original = api_client_module.runtime_tokens
    api_client_module.runtime_tokens = store
    try:
        client = RecordingClient(_settings(tmp_path, access_token="env-token"))
        result = client.query_salesforce("SELECT Id FROM Account")
    finally:
        api_client_module.runtime_tokens = original

    assert result["ok"] is True
    assert client.calls == [
        (
            "GET",
            "https://runtime.my.salesforce.com/services/data/v61.0/query?q=SELECT+Id+FROM+Account",
            "runtime-token",
        )
    ]


def test_api_client_prefers_runtime_datacloud_token(tmp_path: Path) -> None:
    store = RuntimeTokenStore()
    store.set_datacloud(TokenBundle(access_token="runtime-dc-token"))
    import salesforce_mcp.api_client as api_client_module

    original = api_client_module.runtime_tokens
    api_client_module.runtime_tokens = store
    try:
        client = RecordingClient(
            _settings(
                tmp_path,
                datacloud_api_url="https://tenant.example.com",
                datacloud_access_token="env-dc-token",
            )
        )
        result = client.datacloud_submit_query("SELECT 1")
    finally:
        api_client_module.runtime_tokens = original

    assert result["ok"] is True
    assert client.calls == [
        ("POST", "https://tenant.example.com/api/v3/query", "runtime-dc-token")
    ]


def test_clear_runtime_tokens_removes_masked_status() -> None:
    store = RuntimeTokenStore()
    store.set_salesforce(TokenBundle(access_token="runtime-token"))

    result = store.clear()

    assert result["cleared"] is True
    assert store.status()["salesforce"] == {"configured": False}
