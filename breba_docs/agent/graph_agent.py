import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from breba_docs.agent.instruction_reader import get_instructions


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class GraphAgent:

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o-mini")

        self.system_instructions = None
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.invoke_model)

        graph.set_entry_point("llm")
        graph.add_edge("llm", END)

        self.graph = graph.compile()

    def fetch_goals(self, doc: str) -> list[dict]:
        self.system_instructions = get_instructions("identify_goals", document=doc)
        messages = [HumanMessage(content="What are my goals for this document?")]
        goals = self.graph.invoke({"messages": messages})
        return json.loads(goals['messages'][-1].content)["goals"]

    def invoke_model(self, state: AgentState):
        messages = state['messages']
        if self.system_instructions:
            messages = [SystemMessage(content=self.system_instructions)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}
