from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _safe_profile_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return safe or "default"


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if not value:
        return default
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    org_url: str | None
    instance_url: str | None
    access_token: str | None
    api_version: str
    datacloud_query_url: str | None
    datacloud_api_url: str | None
    datacloud_ingestion_url: str | None
    datacloud_access_token: str | None
    oauth_client_id: str | None
    oauth_client_secret: str | None
    oauth_redirect_uri: str
    oauth_scopes: str
    profile: str
    headless: bool
    timeout_ms: int
    viewport_width: int
    viewport_height: int
    auth_dir: Path
    logs_dir: Path
    runs_dir: Path
    journal_redact_fields: tuple[str, ...]

    @property
    def profile_dir(self) -> Path:
        return self.auth_dir / self.profile


def load_settings() -> Settings:
    _load_dotenv(ROOT_DIR / ".env")

    profile = _safe_profile_name(os.getenv("SALESFORCE_PROFILE", "default"))
    return Settings(
        org_url=os.getenv("SALESFORCE_ORG_URL") or None,
        instance_url=os.getenv("SALESFORCE_INSTANCE_URL") or os.getenv("SALESFORCE_ORG_URL") or None,
        access_token=os.getenv("SALESFORCE_ACCESS_TOKEN") or None,
        api_version=os.getenv("SALESFORCE_API_VERSION", "61.0"),
        datacloud_query_url=os.getenv("SALESFORCE_DATACLOUD_QUERY_URL") or None,
        datacloud_api_url=os.getenv("SALESFORCE_DATACLOUD_API_URL") or None,
        datacloud_ingestion_url=os.getenv("SALESFORCE_DATACLOUD_INGESTION_URL") or None,
        datacloud_access_token=os.getenv("SALESFORCE_DATACLOUD_ACCESS_TOKEN")
        or os.getenv("SALESFORCE_ACCESS_TOKEN")
        or None,
        oauth_client_id=os.getenv("SALESFORCE_OAUTH_CLIENT_ID") or None,
        oauth_client_secret=os.getenv("SALESFORCE_OAUTH_CLIENT_SECRET") or None,
        oauth_redirect_uri=os.getenv("SALESFORCE_OAUTH_REDIRECT_URI", "http://localhost:1717/oauth/callback"),
        oauth_scopes=os.getenv("SALESFORCE_OAUTH_SCOPES", "api refresh_token"),
        profile=profile,
        headless=_bool_env("SALESFORCE_HEADLESS", False),
        timeout_ms=_int_env("SALESFORCE_TIMEOUT_MS", 30_000),
        viewport_width=_int_env("SALESFORCE_VIEWPORT_WIDTH", 1440),
        viewport_height=_int_env("SALESFORCE_VIEWPORT_HEIGHT", 1000),
        auth_dir=ROOT_DIR / ".auth",
        logs_dir=ROOT_DIR / "logs",
        runs_dir=ROOT_DIR / "runs",
        journal_redact_fields=_csv_env(
            "SALESFORCE_JOURNAL_REDACT_FIELDS",
            ("token", "password", "secret", "access_token", "refresh_token", "authorization"),
        ),
    )
