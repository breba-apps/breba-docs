from unittest.mock import patch, MagicMock

import pytest
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from breba_docs.agent.build_agent import BuildAgent, State


@pytest.fixture
def build_agent():
    with patch("breba_docs.agent.build_agent.ChatOpenAI", new_callable=MagicMock):
        return BuildAgent()

not_a_valid_prompt_response = [
    "Here is the prompt that works best\nThis is my cool prompt\nCan I help you with anything else?",
    "Please specify the format or masking for the email field.",
    "This is the prompt::final prompt result::",
]

valid_prompt_response = [
    "::final prompt result::Final extracted text",
    "::final prompt result::Final extracted text::final prompt result::",
    "Here is the prompt that works best:::final prompt result::Final extracted text::final prompt result::",
    "::final prompt result::Final extracted text::final prompt result::Can I help you with anything else?",
    "Here is the prompt that works best\n::final prompt result::Final extracted text::final prompt result::\nCan I help you with anything else?",
]

@patch("breba_docs.agent.build_agent.input", return_value="User response")
@pytest.mark.parametrize("prompt_response", valid_prompt_response)
def test_is_final_prompt_valid(mock_input, build_agent, prompt_response):
    """Test that the state correctly transitions to extract_prompt when final prompt is detected."""

    state = State(messages=[
        SystemMessage(content="System message"),
        HumanMessage(content="Some query"),
        AIMessage(content=prompt_response)
    ])

    assert build_agent.is_final_prompt(state) is True, f"Expect True, but got False for content: {prompt_response}"

@patch("breba_docs.agent.build_agent.input", return_value="User response")
@pytest.mark.parametrize("prompt_response", valid_prompt_response)
def test_extract_prompt_valid(mock_input, build_agent, prompt_response):
    """Test that the state correctly transitions to extract_prompt is not detected."""

    state = State(messages=[
        SystemMessage(content="System message"),
        HumanMessage(content="Some query"),
        AIMessage(content=prompt_response)
    ])

    state_update = build_agent.extract_prompt(state)
    prompt = state_update["prompt"]
    assert prompt == "Final extracted text"

@patch("breba_docs.agent.build_agent.input", return_value="User response")
@pytest.mark.parametrize("not_a_prompt", not_a_valid_prompt_response)
def test_is_final_prompt_invalid(mock_input, build_agent, not_a_prompt):
    """Test that the state correctly transitions to extract_prompt is not detected."""

    state = State(messages=[
        SystemMessage(content="System message"),
        HumanMessage(content="Some query"),
        AIMessage(content=not_a_prompt)
    ])

    assert build_agent.is_final_prompt(state) is False, f"Expect False, but got True for content: {not_a_prompt}"

@patch("breba_docs.agent.build_agent.input", return_value="User response")
@pytest.mark.parametrize("not_a_prompt", not_a_valid_prompt_response)
def test_extract_prompt_invalid(mock_input, build_agent, not_a_prompt):
    """Test that the state correctly transitions to extract_prompt is not detected."""

    state = State(messages=[
        SystemMessage(content="System message"),
        HumanMessage(content="Some query"),
        AIMessage(content=not_a_prompt)
    ])

    assert build_agent.extract_prompt(state) == {'prompt': ''}