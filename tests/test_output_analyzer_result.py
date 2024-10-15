import pytest

from breba_docs.services.output_analyzer_result import PASS, OutputAnalyzerResult, UNKNOWN, FAIL


@pytest.mark.parametrize(
    "input_message, expected_success, expected_insights",
    [
        (f"{PASS}, Insight message", True, "Insight message"),
        (f"{FAIL}, Failure message", False, "Failure message"),
        (f"{UNKNOWN}, Unknown state", False, "Unknown state"),
        (f"{PASS}", True, ""),  # Case where no insights are provided
        (f"{FAIL}", False, ""),  # Case where no insights are provided
    ]
)
def test_agent_output_from_string(input_message, expected_success, expected_insights):
    result = OutputAnalyzerResult.from_string(input_message)

    assert result.success == expected_success
    assert result.insights == expected_insights
