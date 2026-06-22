from __future__ import annotations

import os
from pathlib import Path

import pytest

from salesforce_mcp.browser import SalesforceBrowser
from salesforce_mcp.config import Settings


@pytest.mark.skipif(
    os.getenv("RUN_PLAYWRIGHT_SMOKE") != "1",
    reason="Set RUN_PLAYWRIGHT_SMOKE=1 to launch Chromium for the local smoke test.",
)
@pytest.mark.anyio
async def test_playwright_smoke_with_local_html(tmp_path: Path) -> None:
    settings = Settings(
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
        profile="smoke",
        headless=True,
        timeout_ms=10_000,
        viewport_width=900,
        viewport_height=700,
        auth_dir=tmp_path / ".auth",
        logs_dir=tmp_path / "logs",
        runs_dir=tmp_path / "runs",
        journal_redact_fields=("token", "password"),
    )
    html = tmp_path / "page.html"
    html.write_text(
        "<html><title>Smoke</title><body>"
        "<label>Name<input value='' oninput=\"document.getElementById('out').textContent=this.value\"></label>"
        "<div id='out'></div><button>Save</button></body></html>",
        encoding="utf-8",
    )

    browser = SalesforceBrowser(settings)
    try:
        result = await browser.navigate(html.as_uri())
        assert result["title"] == "Smoke"
        result = await browser.fill(label="Name", value="Data Cloud")
        assert "Data Cloud" in result["visible_text"]
        result = await browser.click(text="Save")
        assert result["screenshot_path"]
    finally:
        await browser.close()
