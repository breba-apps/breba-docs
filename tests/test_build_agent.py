import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from breba_docs.agent.build_agent import BuildAgent, State


@pytest.fixture
def build_agent():
    with patch("breba_docs.agent.build_agent.ChatOpenAI", new_callable=MagicMock):
        return BuildAgent()


@patch("breba_docs.agent.build_agent.input", return_value="User response")
def test_is_final_prompt_transition(mock_input, build_agent):
    """Test that the state correctly transitions to extract_prompt when final prompt is detected."""

    state = State(messages=[
        SystemMessage(content="System message"),
        HumanMessage(content="Some query"),
        AIMessage(content="Response::final prompt result::Final extracted text")
    ])

    assert build_agent.is_final_prompt(state) is True
