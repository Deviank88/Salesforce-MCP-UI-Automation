from __future__ import annotations

from salesforce_mcp.assertions import assert_records


def test_assert_records_count_and_contains_pass() -> None:
    result = assert_records(
        {
            "min_count": 1,
            "contains": [{"Id": "001", "Name": "Acme"}],
            "required_fields": ["Id", "Name"],
            "no_errors": True,
        },
        records=[{"Id": "001", "Name": "Acme"}],
    )

    assert result["passed"] is True
    assert result["record_count"] == 1


def test_assert_records_reports_failures() -> None:
    result = assert_records(
        {
            "count_equals": 2,
            "contains": [{"Id": "missing"}],
            "required_fields": ["Name"],
        },
        records=[{"Id": "001"}],
    )

    assert result["passed"] is False
    assert len(result["failures"]) == 3
