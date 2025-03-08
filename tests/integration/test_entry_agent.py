import pytest
from dotenv import load_dotenv

from breba_docs.agent.entry_agent import EntryAgent


@pytest.mark.integration
def test_some_text():
    load_dotenv()
    agent = EntryAgent()
    result = agent.invoke(
        "We are creating a website for generating forms. You will need to produce HTML for entering an email, a phone number and a t-shirt size.")
    assert result is not None