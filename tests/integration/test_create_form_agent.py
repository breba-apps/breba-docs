import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from breba_docs.agent.create_form_agent import CreateFormAgent

initialState = {'next': 'prompt_builder', 'messages': [HumanMessage(content='We are creating a website for generating forms. You will need to produce HTML for entering an email, a phone number and a t-shirt size.', id='c41bacea-2307-469c-be65-e5565fae49a2')]}

@pytest.mark.integration
def test_supervisor_node():

    load_dotenv()
    agent = CreateFormAgent()
    result = agent.supervisor_node(initialState)
    assert result.update["next"] == "prompt_builder"
    assert result.goto == "prompt_builder"


