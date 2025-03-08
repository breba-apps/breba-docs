from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from breba_docs.agent.instruction_reader import get_instructions


@tool
def execute_command(command: str) -> str:
    """Use this to run any command in the terminal"""
    return "Not yet implemented"


class EntryAgent:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0)
        self.graph = create_react_agent(self.model, tools=[execute_command])

    def invoke(self, entry_text: str):
        instructions = get_instructions("entry_agent")
        inputs = {"messages": [
            ("system", instructions),
            ("user", entry_text),
        ]}
        result = self.graph.invoke(inputs, {"recursion_limit": 100})
        return result
