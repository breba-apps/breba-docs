import pytest

from breba_docs.services.output_analyzer_result import OutputAnalyzerResult


def test_agent_output_from_string():
    result = OutputAnalyzerResult.from_string(OutputAnalyzerResult.example_str())

    assert result.success is True
    assert result.command == "git clone https://github.com/Nodestream/nodestream.git"
    assert result.insights == ("The cloning process completed successfully with all objects received and deltas "
                               "resolved.")
