from pathlib import Path

import pytest
from dotenv import load_dotenv

from breba_docs.agent.graph_agent import GraphAgent
from breba_docs.services.document import Document
from breba_docs.services.reports import GoalReport


@pytest.fixture
def agent(doc):
    load_dotenv()
    return GraphAgent(doc)


@pytest.fixture
def doc():
    source_doc = Path("tests/integration/fixtures/typo_doc.md")
    destination_doc_path = Path("tests/integration/fixtures/copy_typo_doc.md")
    destination_doc_path.write_text(source_doc.read_text())

    with open(destination_doc_path, 'r') as file:
        content =  file.read()
        return Document(content, destination_doc_path)


# @pytest.mark.integration
# def test_invoke_graph(mocker, agent, doc):
#     graph = GraphAgent(doc) # agent(doc)
#     state = graph.invoke()
#     goal_reports = state['goal_reports']
#     getting_started_goal_iter = (goal_report for goal_report in goal_reports if goal_report.goal.name == "getting started")
#     getting_started_goal: GoalReport = next(getting_started_goal_iter, None)
#     assert getting_started_goal, "No goal with the name 'getting started' was found in the fetched goal_reports."
#     assert getting_started_goal.command_reports[0].success
#     assert getting_started_goal.command_reports[1].success
#     assert not getting_started_goal.command_reports[2].success
#     assert getting_started_goal.modify_command_reports[0].command =="sed -i '' 's/nodestream run simple -v/nodestream run sample -v/' tests/integration/fixtures/copy_typo_doc.md"
#     assert getting_started_goal.modify_command_reports[0].success == True
#
#     second_goal_report: GoalReport = next(getting_started_goal_iter, None)
#     assert second_goal_report, "After successful modifications in first goal report, should have a second goal report"
#     assert second_goal_report.command_reports[0].success
#     assert second_goal_report.command_reports[1].success
#     assert second_goal_report.command_reports[2].success
#     assert len(second_goal_report.modify_command_reports) == 0



