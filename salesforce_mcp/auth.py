from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

from .config import Settings, load_settings


def _now() -> str:
    return datetime.now(UTC).isoformat()


def create_code_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def create_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _host(url: str | None) -> str:
    return (urlparse(url or "").hostname or "").lower()


@dataclass
class TokenBundle:
    access_token: str
    refresh_token: str | None = None
    instance_url: str | None = None
    token_type: str = "Bearer"
    source: str = "runtime"
    issued_at: str | None = None
    expires_in: int | None = None
    scope: str | None = None
    domain: str | None = None

    def masked(self) -> dict[str, object]:
        return {
            "configured": True,
            "source": self.source,
            "token_type": self.token_type,
            "instance_url": self.instance_url,
            "domain": self.domain,
            "issued_at": self.issued_at,
            "expires_in": self.expires_in,
            "scope": self.scope,
            "has_access_token": bool(self.access_token),
            "has_refresh_token": bool(self.refresh_token),
            "access_token": "***REDACTED***",
            "refresh_token": "***REDACTED***" if self.refresh_token else None,
        }


class RuntimeTokenStore:
    def __init__(self) -> None:
        self._salesforce: TokenBundle | None = None
        self._datacloud: TokenBundle | None = None

    def set_salesforce(self, bundle: TokenBundle, *, use_for_datacloud: bool = False) -> None:
        self._salesforce = bundle
        if use_for_datacloud:
            self._datacloud = bundle

    def set_datacloud(self, bundle: TokenBundle) -> None:
        self._datacloud = bundle

    def clear(self) -> dict[str, object]:
        had_salesforce = self._salesforce is not None
        had_datacloud = self._datacloud is not None
        self._salesforce = None
        self._datacloud = None
        return {"cleared": True, "had_salesforce_token": had_salesforce, "had_datacloud_token": had_datacloud}

    def salesforce(self) -> TokenBundle | None:
        return self._salesforce

    def datacloud(self) -> TokenBundle | None:
        return self._datacloud

    def status(self) -> dict[str, object]:
        return {
            "salesforce": self._salesforce.masked() if self._salesforce else {"configured": False},
            "datacloud": self._datacloud.masked() if self._datacloud else {"configured": False},
        }


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: "_OAuthCallbackServer"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        self.server.oauth_result = {
            "code": (params.get("code") or [None])[0],
            "state": (params.get("state") or [None])[0],
            "error": (params.get("error") or [None])[0],
            "error_description": (params.get("error_description") or [None])[0],
        }
        self.send_response(200 if self.server.oauth_result.get("code") else 400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Salesforce MCP OAuth callback received. You can return to the MCP client.")

    def log_message(self, format: str, *args: object) -> None:
        return


class _OAuthCallbackServer(ThreadingHTTPServer):
    oauth_result: dict[str, str | None] | None = None


class BrowserAuthBridge:
    def __init__(self, settings: Settings | None = None, token_store: RuntimeTokenStore | None = None) -> None:
        self.settings = settings or load_settings()
        self.token_store = token_store or runtime_tokens

    async def browser_auth_status(self, sf_browser: Any) -> dict[str, object]:
        page = await sf_browser.ensure_page()
        cookies = await sf_browser.cookies()
        sid = self.find_sid_cookie(cookies, page.url or self.settings.org_url)
        return {
            "logged_in_hint": bool(sid),
            "current_url": page.url,
            "runtime_tokens": self.token_store.status(),
            "browser_session": self._cookie_status(sid),
            "next_suggested_actions": []
            if sid
            else ["Call open_org, complete login/MFA in Playwright, then call browser_auth_status again."],
        }

    async def use_browser_session_token(self, sf_browser: Any) -> dict[str, object]:
        page = await sf_browser.ensure_page()
        sid = self.find_sid_cookie(await sf_browser.cookies(), page.url or self.settings.org_url)
        if not sid:
            return {
                "ok": False,
                "configured": False,
                "error": "No Salesforce sid cookie found in the active Playwright session.",
                "next_suggested_actions": ["Call open_org, complete login/MFA, then retry use_browser_session_token."],
            }
        bundle = TokenBundle(
            access_token=str(sid["value"]),
            instance_url=self._instance_url_from_cookie(page.url, sid),
            token_type="Bearer",
            source="browser_sid_cookie",
            issued_at=_now(),
            domain=str(sid.get("domain") or ""),
        )
        self.token_store.set_salesforce(bundle)
        return {"ok": True, "configured": True, "salesforce": bundle.masked()}

    async def start_oauth_token_flow(self, sf_browser: Any, timeout_seconds: int = 180) -> dict[str, object]:
        if not self.settings.oauth_client_id:
            return {
                "ok": False,
                "configured": False,
                "error": "Set SALESFORCE_OAUTH_CLIENT_ID to enable OAuth Authorization Code + PKCE.",
            }

        verifier = create_code_verifier()
        state = secrets.token_urlsafe(24)
        redirect = urlparse(self.settings.oauth_redirect_uri)
        server = _OAuthCallbackServer((redirect.hostname or "127.0.0.1", redirect.port or 80), _OAuthCallbackHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            authorize_url = self._authorize_url(verifier, state)
            page = await sf_browser.ensure_page()
            await page.goto(authorize_url, wait_until="domcontentloaded")
            result = await self._wait_for_callback(server, state, timeout_seconds)
        finally:
            server.shutdown()
            server.server_close()

        if result.get("error"):
            return {"ok": False, "configured": True, "error": result.get("error"), "error_description": result.get("error_description")}
        token_result = self.exchange_oauth_code(str(result["code"]), verifier)
        if not token_result.get("ok"):
            return token_result
        data = token_result["data"]
        if not isinstance(data, dict) or not data.get("access_token"):
            return {"ok": False, "configured": True, "error": "OAuth token response did not include an access_token."}
        bundle = TokenBundle(
            access_token=str(data["access_token"]),
            refresh_token=str(data["refresh_token"]) if data.get("refresh_token") else None,
            instance_url=str(data.get("instance_url") or self.settings.instance_url or self.settings.org_url or ""),
            token_type=str(data.get("token_type") or "Bearer"),
            source="oauth_pkce",
            issued_at=str(data.get("issued_at") or _now()),
            scope=str(data.get("scope")) if data.get("scope") else self.settings.oauth_scopes,
            domain=_host(str(data.get("instance_url") or self.settings.org_url or "")),
        )
        self.token_store.set_salesforce(bundle, use_for_datacloud=True)
        return {"ok": True, "configured": True, "salesforce": bundle.masked(), "datacloud": bundle.masked()}

    def refresh_oauth_token(self) -> dict[str, object]:
        current = self.token_store.salesforce()
        if not current or not current.refresh_token:
            return {"ok": False, "configured": False, "error": "No runtime refresh token available. Run start_oauth_token_flow first."}
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.settings.oauth_client_id,
            "refresh_token": current.refresh_token,
        }
        if self.settings.oauth_client_secret:
            payload["client_secret"] = self.settings.oauth_client_secret
        result = self._token_request(payload)
        if not result.get("ok"):
            return result
        data = result["data"]
        if not isinstance(data, dict) or not data.get("access_token"):
            return {"ok": False, "configured": True, "error": "Refresh response did not include an access_token."}
        refreshed = TokenBundle(
            access_token=str(data["access_token"]),
            refresh_token=str(data.get("refresh_token") or current.refresh_token),
            instance_url=str(data.get("instance_url") or current.instance_url or ""),
            token_type=str(data.get("token_type") or current.token_type),
            source="oauth_refresh",
            issued_at=str(data.get("issued_at") or _now()),
            scope=str(data.get("scope")) if data.get("scope") else current.scope,
            domain=current.domain,
        )
        self.token_store.set_salesforce(refreshed, use_for_datacloud=self.token_store.datacloud() is current)
        return {"ok": True, "configured": True, "salesforce": refreshed.masked()}

    def clear_runtime_tokens(self) -> dict[str, object]:
        return self.token_store.clear()

    def exchange_oauth_code(self, code: str, verifier: str) -> dict[str, object]:
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.settings.oauth_client_id,
            "redirect_uri": self.settings.oauth_redirect_uri,
            "code": code,
            "code_verifier": verifier,
        }
        if self.settings.oauth_client_secret:
            payload["client_secret"] = self.settings.oauth_client_secret
        return self._token_request(payload)

    def _authorize_url(self, verifier: str, state: str) -> str:
        base = (self.settings.org_url or self.settings.instance_url or "https://login.salesforce.com").rstrip("/")
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.settings.oauth_client_id,
                "redirect_uri": self.settings.oauth_redirect_uri,
                "scope": self.settings.oauth_scopes,
                "state": state,
                "code_challenge": create_code_challenge(verifier),
                "code_challenge_method": "S256",
            },
            quote_via=quote,
        )
        return f"{base}/services/oauth2/authorize?{query}"

    async def _wait_for_callback(
        self,
        server: _OAuthCallbackServer,
        expected_state: str,
        timeout_seconds: int,
    ) -> dict[str, str | None]:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            if server.oauth_result:
                if server.oauth_result.get("state") != expected_state:
                    return {"error": "invalid_state", "error_description": "OAuth callback state did not match."}
                return server.oauth_result
            await asyncio.sleep(0.25)
        return {"error": "timeout", "error_description": "OAuth callback was not received before timeout."}

    def _token_request(self, payload: dict[str, str | None]) -> dict[str, object]:
        if not self.settings.oauth_client_id:
            return {"ok": False, "configured": False, "error": "Set SALESFORCE_OAUTH_CLIENT_ID first."}
        base = (self.settings.org_url or self.settings.instance_url or "https://login.salesforce.com").rstrip("/")
        request = Request(
            f"{base}/services/oauth2/token",
            data=urlencode({key: value for key, value in payload.items() if value is not None}).encode("utf-8"),
            method="POST",
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return {"ok": True, "configured": True, "status_code": response.status, "data": json.loads(raw) if raw else {}}
        except HTTPError as exc:
            return {"ok": False, "configured": True, "status_code": exc.code, "error": exc.read().decode("utf-8", errors="replace")}
        except (URLError, TimeoutError) as exc:
            return {"ok": False, "configured": True, "status_code": None, "error": str(exc)}

    def find_sid_cookie(self, cookies: list[dict[str, Any]], org_url: str | None) -> dict[str, Any] | None:
        host = _host(org_url)
        matches = [cookie for cookie in cookies if cookie.get("name") == "sid" and cookie.get("value")]
        if host:
            for cookie in matches:
                domain = str(cookie.get("domain") or "").lstrip(".").lower()
                if domain and (host == domain or host.endswith("." + domain) or domain.endswith(host)):
                    return cookie
        return matches[0] if matches else None

    def _cookie_status(self, cookie: dict[str, Any] | None) -> dict[str, object]:
        if not cookie:
            return {"configured": False, "has_sid_cookie": False}
        return {
            "configured": True,
            "has_sid_cookie": True,
            "domain": cookie.get("domain"),
            "expires": cookie.get("expires"),
            "http_only": cookie.get("httpOnly"),
            "secure": cookie.get("secure"),
            "same_site": cookie.get("sameSite"),
            "access_token": "***REDACTED***",
        }

    def _instance_url_from_cookie(self, current_url: str, cookie: dict[str, Any]) -> str:
        if current_url and _host(current_url):
            parsed = urlparse(current_url)
            return f"{parsed.scheme}://{parsed.netloc}"
        domain = str(cookie.get("domain") or "").lstrip(".")
        return f"https://{domain}" if domain else str(self.settings.instance_url or self.settings.org_url or "")


runtime_tokens = RuntimeTokenStore()
auth_bridge = BrowserAuthBridge(token_store=runtime_tokens)
