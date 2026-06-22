from __future__ import annotations

from salesforce_mcp.output import ToolResult


def test_tool_result_shape_is_stable() -> None:
    result = ToolResult(
        url="https://example.my.salesforce.com",
        title="Salesforce",
        visible_text="Setup",
        screenshot_path="logs/snapshot.png",
        warnings=["login required"],
        next_suggested_actions=["retry"],
    ).to_dict()

    assert set(result) == {
        "url",
        "title",
        "visible_text",
        "screenshot_path",
        "warnings",
        "next_suggested_actions",
    }
