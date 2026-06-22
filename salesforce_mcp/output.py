from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolResult:
    url: str = ""
    title: str = ""
    visible_text: str = ""
    screenshot_path: str | None = None
    warnings: list[str] = field(default_factory=list)
    next_suggested_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "title": self.title,
            "visible_text": self.visible_text,
            "screenshot_path": self.screenshot_path,
            "warnings": self.warnings,
            "next_suggested_actions": self.next_suggested_actions,
        }


def path_to_str(path: Path | None) -> str | None:
    return str(path) if path else None
