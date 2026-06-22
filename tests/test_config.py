from __future__ import annotations

from pathlib import Path

from salesforce_mcp.config import Settings, _safe_profile_name


def test_safe_profile_name_removes_path_characters() -> None:
    assert _safe_profile_name("../client org") == "___client_org"
    assert _safe_profile_name("") == "default"


def test_profile_dir_uses_auth_dir() -> None:
    settings = Settings(
        org_url="https://example.my.salesforce.com",
        instance_url="https://example.my.salesforce.com",
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
        profile="client_a",
        headless=False,
        timeout_ms=30_000,
        viewport_width=1440,
        viewport_height=1000,
        auth_dir=Path(".auth"),
        logs_dir=Path("logs"),
        runs_dir=Path("runs"),
        journal_redact_fields=("token", "password"),
    )

    assert settings.profile_dir == Path(".auth") / "client_a"
