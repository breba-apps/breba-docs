from breba_docs.services.reports import CommandReport


def test_agent_output_from_string():
    result = CommandReport.from_string(CommandReport.example_str())

    assert result.success is True
    assert result.command == "git clone https://github.com/Nodestream/nodestream.git"
    assert result.insights == ("The cloning process completed successfully with all objects received and deltas "
                               "resolved.")
