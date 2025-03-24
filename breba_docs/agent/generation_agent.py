from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from breba_docs.agent.instruction_reader import get_instructions


# Define the structure of our state
class State(TypedDict):
    content: str


@tool
def web_search_preview(location: str):
    """Process web search results"""
    return "Hot and Sunny every day"


class GenerationAgent:

    def __init__(self):
        self.system_prompt = get_instructions("generation_agent")

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        self.model = llm.bind_tools([{"type": "web_search_preview"}])
        self.final_state = None

    def stream(self, user_input: str):
        return self.model.invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input),
        ]
        )

    def invoke(self, user_input: str) -> State:
        response = self.model.invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input),
        ])
        return {"content": response.content[0]["text"]}


if __name__ == "__main__":
    load_dotenv()
    agent = GenerationAgent()

    response = agent.invoke(
        "This website will show current weather for Stevens Pass.")

    print(response)
