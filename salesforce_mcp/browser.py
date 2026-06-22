from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from .config import Settings, load_settings
from .guardrails import guard_dangerous_action
from .output import ToolResult, path_to_str


SETUP_PATH = "/lightning/setup/SetupOneHome/home"

DATACLOUD_AREAS = {
    "home": "Data Cloud",
    "data_cloud": "Data Cloud",
    "data streams": "Data Streams",
    "data_streams": "Data Streams",
    "data spaces": "Data Spaces",
    "data_spaces": "Data Spaces",
    "identity resolution": "Identity Resolution",
    "identity_resolution": "Identity Resolution",
    "calculated insights": "Calculated Insights",
    "calculated_insights": "Calculated Insights",
    "data actions": "Data Actions",
    "data_actions": "Data Actions",
}


class SalesforceBrowser:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._logger: logging.Logger | None = None
        self._lock = asyncio.Lock()

    @property
    def logger(self) -> logging.Logger:
        if self._logger is not None:
            return self._logger

        logger = logging.getLogger("salesforce_mcp")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if logger.handlers:
            self._logger = logger
            return logger

        self.settings.logs_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(self.settings.logs_dir / "operations.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        self._logger = logger
        return logger

    async def ensure_page(self) -> Page:
        async with self._lock:
            if self._page and not self._page.is_closed():
                return self._page

            self.settings.profile_dir.mkdir(parents=True, exist_ok=True)
            self.settings.logs_dir.mkdir(parents=True, exist_ok=True)

            self._playwright = await async_playwright().start()
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.settings.profile_dir),
                headless=self.settings.headless,
                viewport={
                    "width": self.settings.viewport_width,
                    "height": self.settings.viewport_height,
                },
                accept_downloads=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            self._context.set_default_timeout(self.settings.timeout_ms)
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
            self.logger.info("Browser started profile=%s headless=%s", self.settings.profile, self.settings.headless)
            return self._page

    async def close(self) -> dict[str, object]:
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._context = None
        self._playwright = None
        self._page = None
        self.logger.info("Browser closed")
        return {
            "url": "",
            "title": "",
            "visible_text": "Browser closed.",
            "screenshot_path": None,
            "warnings": [],
            "next_suggested_actions": ["Call open_org to start a new Salesforce browser session."],
        }

    async def open_org(self, org_url: str | None = None) -> dict[str, object]:
        target = org_url or self.settings.org_url
        if not target:
            raise ValueError("No org URL provided. Set SALESFORCE_ORG_URL or pass org_url.")
        page = await self.ensure_page()
        await page.goto(target, wait_until="domcontentloaded")
        await self._settle(page)
        self.logger.info("Opened org url=%s", target)
        return await self.snapshot(include_screenshot=True)

    async def navigate(self, url: str) -> dict[str, object]:
        page = await self.ensure_page()
        await page.goto(url, wait_until="domcontentloaded")
        await self._settle(page)
        self.logger.info("Navigated url=%s", url)
        return await self.snapshot(include_screenshot=True)

    async def cookies(self, urls: list[str] | None = None) -> list[dict[str, object]]:
        page = await self.ensure_page()
        context = self._context
        if context is None:
            return []
        target_urls = urls or ([page.url] if page.url else None)
        return await context.cookies(target_urls)

    async def snapshot(
        self,
        include_screenshot: bool = False,
        max_text_chars: int = 6000,
        include_dom: bool = False,
        include_iframes: bool = True,
    ) -> dict[str, object]:
        page = await self.ensure_page()
        await self._settle(page)

        warnings: list[str] = []
        screenshot_path: Path | None = None
        if include_screenshot:
            screenshot_path = await self._screenshot(page, "snapshot")

        text = await self._visible_text(page, max_text_chars)
        iframe_text = await self._iframe_text(page, max_text_chars=max_text_chars // 2) if include_iframes else []
        title = await page.title()
        url = page.url

        if self._looks_logged_out(url, text):
            warnings.append("Salesforce session appears unauthenticated or expired. Complete login/MFA in the browser.")

        result = ToolResult(
            url=url,
            title=title,
            visible_text=text,
            screenshot_path=path_to_str(screenshot_path),
            warnings=warnings,
            next_suggested_actions=self._suggest_next_actions(url, text),
        ).to_dict()
        result["failure_classification"] = self.classify_failure(url, text, warnings)
        if include_dom:
            result["dom"] = await self._dom_snapshot(page)
        if iframe_text:
            result["iframes"] = iframe_text
        return result

    async def click(
        self,
        text: str | None = None,
        selector: str | None = None,
        role: str | None = None,
        name: str | None = None,
        exact: bool = False,
        confirm_dangerous: bool = False,
    ) -> dict[str, object]:
        warnings = guard_dangerous_action(confirm_dangerous, text, selector, role, name)
        page = await self.ensure_page()

        locator = self._locator(page, text=text, selector=selector, role=role, name=name, exact=exact)
        await locator.first.click()
        await self._settle(page)
        screenshot_path = await self._screenshot(page, "click")
        self.logger.info("Clicked text=%r selector=%r role=%r name=%r", text, selector, role, name)

        result = await self.snapshot(include_screenshot=False)
        result["screenshot_path"] = path_to_str(screenshot_path)
        result["warnings"] = warnings + list(result.get("warnings", []))
        return result

    async def fill(
        self,
        value: str,
        label: str | None = None,
        selector: str | None = None,
        placeholder: str | None = None,
        confirm_dangerous: bool = False,
    ) -> dict[str, object]:
        warnings = guard_dangerous_action(confirm_dangerous, label, selector, placeholder, value)
        page = await self.ensure_page()

        if selector:
            locator = page.locator(selector)
        elif label:
            locator = page.get_by_label(label)
        elif placeholder:
            locator = page.get_by_placeholder(placeholder)
        else:
            raise ValueError("Provide one of selector, label, or placeholder.")

        await locator.first.fill(value)
        await self._settle(page)
        screenshot_path = await self._screenshot(page, "fill")
        self.logger.info("Filled label=%r selector=%r placeholder=%r", label, selector, placeholder)

        result = await self.snapshot(include_screenshot=False)
        result["screenshot_path"] = path_to_str(screenshot_path)
        result["warnings"] = warnings + list(result.get("warnings", []))
        return result

    async def select(
        self,
        value: str | None = None,
        label: str | None = None,
        selector: str | None = None,
        option_label: str | None = None,
    ) -> dict[str, object]:
        page = await self.ensure_page()
        if not selector and not label:
            raise ValueError("Provide selector or label.")
        locator = page.locator(selector) if selector else page.get_by_label(label or "")
        await locator.first.select_option(value=value, label=option_label)
        await self._settle(page)
        screenshot_path = await self._screenshot(page, "select")
        self.logger.info("Selected selector=%r label=%r value=%r option_label=%r", selector, label, value, option_label)

        result = await self.snapshot(include_screenshot=False)
        result["screenshot_path"] = path_to_str(screenshot_path)
        return result

    async def wait_for(
        self,
        selector: str | None = None,
        text: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, object]:
        page = await self.ensure_page()
        timeout = timeout_ms or self.settings.timeout_ms
        if selector:
            await page.locator(selector).first.wait_for(timeout=timeout)
        elif text:
            await page.get_by_text(text).first.wait_for(timeout=timeout)
        else:
            await self._settle(page)
        self.logger.info("Wait completed selector=%r text=%r", selector, text)
        return await self.snapshot(include_screenshot=False)

    async def search_setup(self, query: str) -> dict[str, object]:
        page = await self.ensure_page()
        await self._open_setup(page)

        tried: list[str] = []
        search_locators = [
            page.get_by_placeholder("Quick Find"),
            page.get_by_placeholder("Cerca veloce"),
            page.locator("input[placeholder*='Quick Find']"),
            page.locator("input[placeholder*='Search Setup']"),
            page.locator("input[aria-label*='Quick Find']"),
        ]

        for locator in search_locators:
            try:
                await locator.first.fill(query, timeout=3500)
                await self._settle(page)
                self.logger.info("Setup search query=%r", query)
                result = await self.snapshot(include_screenshot=True)
                result["next_suggested_actions"] = [
                    "Click the matching Setup result, or call open_datacloud_area with a known Data Cloud area."
                ]
                return result
            except PlaywrightTimeoutError:
                tried.append(str(locator))

        result = await self.snapshot(include_screenshot=True)
        result["warnings"] = list(result.get("warnings", [])) + [
            "Setup search input was not found. Salesforce UI may still be loading or localized differently."
        ]
        result["next_suggested_actions"] = [
            "Use snapshot to inspect visible labels, then call click/fill with the visible Salesforce selector."
        ]
        return result

    async def open_datacloud_area(self, area: str = "home") -> dict[str, object]:
        normalized = area.strip().lower().replace("-", "_")
        query = DATACLOUD_AREAS.get(normalized, area)
        result = await self.search_setup(query)
        result["next_suggested_actions"] = [
            f"Open the visible '{query}' result with click(text=...).",
            "Call diagnose_datacloud after the Data Cloud page opens.",
        ]
        return result

    async def diagnose_datacloud(self) -> dict[str, object]:
        result = await self.snapshot(include_screenshot=True, max_text_chars=9000)
        text = str(result.get("visible_text", "")).lower()
        warnings = list(result.get("warnings", []))

        if "data cloud" not in text and "datacloud" not in text:
            warnings.append("Current page does not visibly look like a Data Cloud page.")
        if "permission" in text or "insufficient privileges" in text or "autorizz" in text:
            warnings.append("The page appears to mention permissions or insufficient access.")

        result["warnings"] = warnings
        result["next_suggested_actions"] = [
            "Capture the exact visible error or setup section with snapshot.",
            "If logged out, complete login/MFA manually and retry.",
            "If permissions are missing, verify the user's Data Cloud and Setup permissions.",
        ]
        self.logger.info("Data Cloud diagnosis captured")
        return result

    def classify_failure(self, url: str, visible_text: str, warnings: list[str] | None = None) -> dict[str, object]:
        text = visible_text.lower()
        combined = f"{url}\n{text}"
        if self._looks_logged_out(url, visible_text):
            return {"type": "login_expired", "recoverable": True}
        if "insufficient privileges" in text or "permission" in text or "autorizz" in text:
            return {"type": "permissions", "recoverable": False}
        if "can't access" in text or "not available" in text or "non disponibile" in text:
            return {"type": "feature_unavailable", "recoverable": False}
        if warnings:
            return {"type": "warning", "recoverable": True}
        if "setup" in combined or "data cloud" in text:
            return {"type": "none", "recoverable": True}
        return {"type": "unknown", "recoverable": True}

    async def _open_setup(self, page: Page) -> None:
        base_url = self.settings.org_url
        if not base_url:
            current = page.url
            if ".salesforce.com" in current:
                base_url = current.split("/lightning/")[0].split("/setup/")[0]
        if not base_url:
            raise ValueError("Cannot infer Salesforce org URL. Call open_org first or set SALESFORCE_ORG_URL.")

        await page.goto(base_url.rstrip("/") + SETUP_PATH, wait_until="domcontentloaded")
        await self._settle(page)

    def _locator(
        self,
        page: Page,
        text: str | None,
        selector: str | None,
        role: str | None,
        name: str | None,
        exact: bool,
    ) -> Any:
        provided = [value is not None for value in (text, selector, role)]
        if sum(provided) != 1:
            raise ValueError("Provide exactly one of text, selector, or role.")
        if selector:
            return page.locator(selector)
        if role:
            role_name = name or text
            if not role_name:
                raise ValueError("Role lookup requires name or text.")
            return page.get_by_role(role, name=role_name, exact=exact)
        return page.get_by_text(text or "", exact=exact)

    async def _settle(self, page: Page) -> None:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=self.settings.timeout_ms)
        except PlaywrightTimeoutError:
            pass
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass

    async def _visible_text(self, page: Page, max_chars: int) -> str:
        try:
            text = await page.locator("body").inner_text(timeout=5000)
        except PlaywrightTimeoutError:
            return ""
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if len(text) > max_chars:
            return text[:max_chars] + "\n...[truncated]"
        return text

    async def _iframe_text(self, page: Page, max_text_chars: int) -> list[dict[str, str]]:
        frames: list[dict[str, str]] = []
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                text = await frame.locator("body").inner_text(timeout=1500)
            except PlaywrightTimeoutError:
                continue
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            if len(text) > max_text_chars:
                text = text[:max_text_chars] + "\n...[truncated]"
            frames.append({"url": frame.url, "visible_text": text})
        return frames

    async def _dom_snapshot(self, page: Page, max_chars: int = 25_000) -> str:
        try:
            html = await page.locator("body").evaluate("element => element.outerHTML")
        except PlaywrightTimeoutError:
            return ""
        if len(html) > max_chars:
            return html[:max_chars] + "\n...[truncated]"
        return html

    async def _screenshot(self, page: Page, prefix: str) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        path = self.settings.logs_dir / f"{timestamp}_{prefix}.png"
        await page.screenshot(path=str(path), full_page=True)
        self.logger.info("Screenshot saved path=%s", path)
        return path

    def _looks_logged_out(self, url: str, visible_text: str) -> bool:
        combined = f"{url}\n{visible_text}".lower()
        return any(
            marker in combined
            for marker in (
                "login.salesforce.com",
                "/secur/login",
                "verify your identity",
                "verification code",
                "single sign-on",
                "password",
            )
        )

    def _suggest_next_actions(self, url: str, visible_text: str) -> list[str]:
        text = visible_text.lower()
        if self._looks_logged_out(url, visible_text):
            return ["Complete login/MFA manually in the Playwright browser, then call snapshot again."]
        if "setup" in url.lower():
            return ["Use search_setup or click a visible Setup item."]
        if "data cloud" in text:
            return ["Call diagnose_datacloud to collect Data Cloud-specific state."]
        return ["Use snapshot with include_screenshot=true, then call click/fill/search_setup as needed."]


browser = SalesforceBrowser()
