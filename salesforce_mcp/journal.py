from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .config import Settings, load_settings


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_run_id() -> str:
    return "run_" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S_") + uuid4().hex[:8]


def _redact(value: object, fields: tuple[str, ...]) -> object:
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            normalized = str(key).lower()
            redacted[key] = "***REDACTED***" if any(field in normalized for field in fields) else _redact(item, fields)
        return redacted
    if isinstance(value, list):
        return [_redact(item, fields) for item in value]
    return value


@dataclass
class RunStep:
    id: str
    type: str
    description: str
    input: dict[str, object] = field(default_factory=dict)
    status: str = "planned"
    requires_approval: bool = False
    approved: bool = False
    attempts: int = 0
    output: dict[str, object] = field(default_factory=dict)
    error: str | None = None
    resources: list[dict[str, object]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class RunJournal:
    run_id: str
    request: str
    target_area: str
    workflow: str
    dry_run: bool
    status: str = "planned"
    max_attempts: int = 3
    recommendation: str = "human_review"
    steps: list[RunStep] = field(default_factory=list)
    resources: list[dict[str, object]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class JournalStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.root = self.settings.runs_dir

    def create(self, journal: RunJournal) -> RunJournal:
        self._write(journal)
        return journal

    def load(self, run_id: str) -> RunJournal:
        path = self._path(run_id)
        if not path.exists():
            raise ValueError(f"Run not found: {run_id}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        steps = [RunStep(**step) for step in raw.pop("steps", [])]
        journal = RunJournal(**raw)
        journal.steps = steps
        return journal

    def save(self, journal: RunJournal) -> RunJournal:
        journal.updated_at = utc_now()
        self._write(journal)
        return journal

    def approve_step(self, run_id: str, step_id: str) -> RunJournal:
        journal = self.load(run_id)
        for step in journal.steps:
            if step.id == step_id:
                step.approved = True
                step.status = "approved"
                step.updated_at = utc_now()
                return self.save(journal)
        raise ValueError(f"Step not found: {step_id}")

    def _path(self, run_id: str) -> Path:
        return self.root / run_id / "run.json"

    def _write(self, journal: RunJournal) -> None:
        path = self._path(journal.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _redact(journal.to_dict(), self.settings.journal_redact_fields)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


store = JournalStore()
