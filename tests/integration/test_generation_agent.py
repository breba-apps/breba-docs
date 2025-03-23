import pytest
from dotenv import load_dotenv

from breba_docs.agent.generation_agent import GenerationAgent


@pytest.mark.integration
def test_generation():
    load_dotenv()
    agent = GenerationAgent()
    result = agent.invoke("This website will show weather forecast for Stevens Pass.")
    assert result["messages"][-1].content is not None
