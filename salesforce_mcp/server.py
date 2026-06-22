from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP

from .api_client import api_client
from .assertions import assert_records as run_record_assertion
from .auth import auth_bridge
from .browser import browser
from .execution import engine


mcp = FastMCP("salesforce-ui-automation")


@mcp.tool()
async def open_org(org_url: str | None = None) -> dict[str, object]:
    """Open a Salesforce org URL with the persistent browser profile."""
    return await browser.open_org(org_url=org_url)


@mcp.tool()
async def snapshot(
    include_screenshot: bool = False,
    max_text_chars: int = 6000,
    include_dom: bool = False,
    include_iframes: bool = True,
) -> dict[str, object]:
    """Return the current page state, visible text, optional screenshot, warnings, and next actions."""
    return await browser.snapshot(
        include_screenshot=include_screenshot,
        max_text_chars=max_text_chars,
        include_dom=include_dom,
        include_iframes=include_iframes,
    )


@mcp.tool()
async def click(
    text: str | None = None,
    selector: str | None = None,
    role: str | None = None,
    name: str | None = None,
    exact: bool = False,
    confirm_dangerous: bool = False,
) -> dict[str, object]:
    """Click a visible element by text, CSS selector, or accessibility role."""
    return await browser.click(
        text=text,
        selector=selector,
        role=role,
        name=name,
        exact=exact,
        confirm_dangerous=confirm_dangerous,
    )


@mcp.tool()
async def fill(
    value: Annotated[str, "Value to enter into the field."],
    label: str | None = None,
    selector: str | None = None,
    placeholder: str | None = None,
    confirm_dangerous: bool = False,
) -> dict[str, object]:
    """Fill an input by label, CSS selector, or placeholder."""
    return await browser.fill(
        value=value,
        label=label,
        selector=selector,
        placeholder=placeholder,
        confirm_dangerous=confirm_dangerous,
    )


@mcp.tool()
async def select(
    value: str | None = None,
    label: str | None = None,
    selector: str | None = None,
    option_label: str | None = None,
) -> dict[str, object]:
    """Select an option in a native select field by selector or label."""
    return await browser.select(value=value, label=label, selector=selector, option_label=option_label)


@mcp.tool()
async def wait_for(
    selector: str | None = None,
    text: str | None = None,
    timeout_ms: int | None = None,
) -> dict[str, object]:
    """Wait for page stability, a selector, or visible text."""
    return await browser.wait_for(selector=selector, text=text, timeout_ms=timeout_ms)


@mcp.tool()
async def search_setup(query: str) -> dict[str, object]:
    """Open Salesforce Setup and search the Quick Find box."""
    return await browser.search_setup(query=query)


@mcp.tool()
async def open_datacloud_area(area: str = "home") -> dict[str, object]:
    """Search Setup for a known Data Cloud area such as Data Streams or Identity Resolution."""
    return await browser.open_datacloud_area(area=area)


@mcp.tool()
async def diagnose_datacloud() -> dict[str, object]:
    """Collect a Data Cloud-oriented diagnostic snapshot of the current page."""
    return await browser.diagnose_datacloud()


@mcp.tool()
async def close_browser() -> dict[str, object]:
    """Close the persistent browser context for the current MCP server process."""
    return await browser.close()


@mcp.tool()
async def browser_auth_status() -> dict[str, object]:
    """Report masked browser/runtime authentication status for the active Playwright session."""
    return await auth_bridge.browser_auth_status(browser)


@mcp.tool()
async def use_browser_session_token() -> dict[str, object]:
    """Use the Salesforce sid cookie from Playwright as an in-memory API session token."""
    return await auth_bridge.use_browser_session_token(browser)


@mcp.tool()
async def start_oauth_token_flow(timeout_seconds: int = 180) -> dict[str, object]:
    """Start OAuth Authorization Code + PKCE in Playwright and store tokens in memory."""
    return await auth_bridge.start_oauth_token_flow(browser, timeout_seconds=timeout_seconds)


@mcp.tool()
async def refresh_oauth_token() -> dict[str, object]:
    """Refresh the in-memory OAuth access token using the runtime refresh token."""
    return auth_bridge.refresh_oauth_token()


@mcp.tool()
async def clear_runtime_tokens() -> dict[str, object]:
    """Clear in-memory Salesforce and Data Cloud runtime tokens."""
    return auth_bridge.clear_runtime_tokens()


@mcp.tool()
async def plan_request(request: str, target_area: str = "data_streams", dry_run: bool = True) -> dict[str, object]:
    """Create a supervised execution plan and run journal for a user request."""
    return engine.plan_request(request=request, target_area=target_area, dry_run=dry_run)


@mcp.tool()
async def list_capabilities() -> dict[str, object]:
    """List supported supervised Data Cloud workflow capabilities."""
    return engine.list_capabilities()


@mcp.tool()
async def execute_plan(run_id: str, max_attempts: int = 3) -> dict[str, object]:
    """Execute a planned run until completion, failure, or approval is required."""
    return await engine.execute_plan(run_id=run_id, max_attempts=max_attempts)


@mcp.tool()
async def get_run_status(run_id: str) -> dict[str, object]:
    """Return the current run journal state."""
    return engine.get_run_status(run_id=run_id)


@mcp.tool()
async def approve_step(run_id: str, step_id: str) -> dict[str, object]:
    """Approve one supervised run step."""
    return engine.approve_step(run_id=run_id, step_id=step_id)


@mcp.tool()
async def rollback_run(run_id: str, mode: str = "safe", confirm_dangerous: bool = False) -> dict[str, object]:
    """Prepare or execute rollback for resources tracked in a run journal."""
    return await engine.rollback_run(run_id=run_id, mode=mode, confirm_dangerous=confirm_dangerous)


@mcp.tool()
async def query_salesforce(soql: str) -> dict[str, object]:
    """Run a Salesforce SOQL query using configured OAuth access token environment variables."""
    return api_client.query_salesforce(soql=soql)


@mcp.tool()
async def query_datacloud(sql_or_query: str) -> dict[str, object]:
    """Run a Data Cloud query against the configured Data Cloud query endpoint."""
    return api_client.query_datacloud(sql_or_query=sql_or_query)


@mcp.tool()
async def datacloud_submit_query(sql: str, mode: str = "ADAPTIVE") -> dict[str, object]:
    """Submit a Data Cloud SQL query and return query metadata or a query id."""
    return api_client.datacloud_submit_query(sql=sql, mode=mode)


@mcp.tool()
async def datacloud_query_status(query_id: str) -> dict[str, object]:
    """Return status for a submitted Data Cloud SQL query."""
    return api_client.datacloud_query_status(query_id=query_id)


@mcp.tool()
async def datacloud_query_rows(query_id: str, offset: int = 0, row_limit: int = 1000) -> dict[str, object]:
    """Return paginated rows for a submitted Data Cloud SQL query."""
    return api_client.datacloud_query_rows(query_id=query_id, offset=offset, row_limit=row_limit)


@mcp.tool()
async def datacloud_cancel_query(query_id: str) -> dict[str, object]:
    """Cancel a submitted Data Cloud SQL query."""
    return api_client.datacloud_cancel_query(query_id=query_id)


@mcp.tool()
async def datacloud_metadata(
    entity_type: str | None = None,
    entity_category: str | None = None,
    entity_name: str | None = None,
) -> dict[str, object]:
    """Retrieve Data Cloud metadata for DLOs, DMOs, Calculated Insights, fields, and relationships."""
    return api_client.datacloud_metadata(
        entity_type=entity_type,
        entity_category=entity_category,
        entity_name=entity_name,
    )


@mcp.tool()
async def assert_records(assertion: dict[str, object], records: list[dict[str, object]] | None = None) -> dict[str, object]:
    """Validate records with count, contains, required field, freshness, and no-error checks."""
    return run_record_assertion(dict(assertion), records=records)


@mcp.tool()
async def compare_before_after(run_id: str) -> dict[str, object]:
    """Compare before/after query evidence captured in a run journal."""
    return engine.compare_before_after(run_id=run_id)


def run() -> None:
    mcp.run()
