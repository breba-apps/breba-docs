import pytest
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from breba_docs.agent.generation_agent import GenerationAgent


@pytest.mark.integration
def test_generation_produces_valid_html():
    load_dotenv()
    agent = GenerationAgent()
    result = agent.invoke("This website will show weather forecast for Stevens Pass.")
    html_content = result["messages"][-1].content

    # Ensure there is content
    assert html_content is not None

    # Parse HTML and ensure it has a <html> and <body> tag
    soup = BeautifulSoup(html_content, "html.parser")

    # Check the structure
    assert soup.html is not None, "HTML tag is missing"
    assert soup.body is not None, "Body tag is missing"
