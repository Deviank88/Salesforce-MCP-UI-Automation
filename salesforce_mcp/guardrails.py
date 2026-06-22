from __future__ import annotations


DANGEROUS_WORDS = {
    "delete",
    "remove",
    "deactivate",
    "disable",
    "drop",
    "truncate",
    "reset",
    "overwrite",
    "archive",
    "elimina",
    "rimuovi",
    "disattiva",
    "cancella",
}


def requires_confirmation(*values: str | None) -> bool:
    haystack = " ".join(value or "" for value in values).lower()
    return any(word in haystack for word in DANGEROUS_WORDS)


def guard_dangerous_action(confirm_dangerous: bool, *values: str | None) -> list[str]:
    if requires_confirmation(*values) and not confirm_dangerous:
        raise ValueError(
            "Potentially destructive action blocked. Retry with confirm_dangerous=true "
            "only after verifying the target action in Salesforce."
        )
    if confirm_dangerous:
        return ["Dangerous action confirmation was explicitly provided."]
    return []
