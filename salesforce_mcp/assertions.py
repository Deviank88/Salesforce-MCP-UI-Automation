from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


def _records_from(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        records = value.get("records")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]
        data = value.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    return []


def _value_at(record: dict[str, Any], field: str) -> Any:
    current: Any = record
    for part in field.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def assert_records(assertion: dict[str, Any], records: Any | None = None) -> dict[str, object]:
    checked_records = _records_from(records if records is not None else assertion.get("records"))
    failures: list[str] = []
    warnings: list[str] = []

    count = len(checked_records)
    if "count_equals" in assertion and count != int(assertion["count_equals"]):
        failures.append(f"Expected exactly {assertion['count_equals']} records, found {count}.")
    if "min_count" in assertion and count < int(assertion["min_count"]):
        failures.append(f"Expected at least {assertion['min_count']} records, found {count}.")
    if "max_count" in assertion and count > int(assertion["max_count"]):
        failures.append(f"Expected at most {assertion['max_count']} records, found {count}.")

    for field_name in assertion.get("required_fields", []) or []:
        missing = [idx for idx, record in enumerate(checked_records) if _value_at(record, str(field_name)) in (None, "")]
        if missing:
            failures.append(f"Field '{field_name}' is missing or empty in record indexes {missing}.")

    for expected in assertion.get("contains", []) or []:
        if not isinstance(expected, dict):
            warnings.append(f"Ignored non-object contains assertion: {expected!r}.")
            continue
        matched = any(all(_value_at(record, key) == value for key, value in expected.items()) for record in checked_records)
        if not matched:
            failures.append(f"No record matched expected values {expected}.")

    freshness_field = assertion.get("freshness_field")
    max_age_minutes = assertion.get("max_age_minutes")
    if freshness_field and max_age_minutes is not None:
        cutoff = datetime.now(UTC) - timedelta(minutes=int(max_age_minutes))
        fresh = False
        for record in checked_records:
            raw_value = _value_at(record, str(freshness_field))
            if not raw_value:
                continue
            try:
                parsed = datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
            except ValueError:
                warnings.append(f"Could not parse freshness value {raw_value!r}.")
                continue
            if parsed >= cutoff:
                fresh = True
                break
        if not fresh:
            failures.append(f"No record is fresh enough on field '{freshness_field}'.")

    if assertion.get("no_errors", False):
        error_markers = ("error", "errors", "exception")
        for idx, record in enumerate(checked_records):
            if any(marker in {key.lower() for key in record} for marker in error_markers):
                failures.append(f"Record index {idx} contains an error marker.")

    return {
        "passed": not failures,
        "record_count": count,
        "failures": failures,
        "warnings": warnings,
    }
