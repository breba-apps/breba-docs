import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from breba_docs.agent.instruction_reader import get_instructions


class AgentState(TypedDict):
    messages: list[AnyMessage]
    goals: list[dict]


class GraphAgent:

    def __init__(self, doc: str):
        self.model = ChatOpenAI(model="gpt-4o-mini")
        self.doc = doc

        self.system_instructions = None
        graph = StateGraph(AgentState)
        graph.add_node("identify_goals", self.identify_goals)
        graph.add_node("identify_commands", self.identify_commands)

        graph.set_entry_point("identify_goals")
        graph.add_edge("identify_goals", "identify_commands")
        graph.add_edge("identify_commands", END)

        self.graph = graph.compile()


    def identify_commands(self, state: AgentState):
        system_instructions = get_instructions("fetch_commands", document=self.doc)
        messages = [SystemMessage(content=system_instructions)]

        for goal in state['goals']:
            message = HumanMessage(content=f"Give me commands for this goal: {json.dumps(goal)}")
            messages = messages + [message]
            message = self.model.invoke(messages)
            messages.append(message)
            commands =[cmd.strip() for cmd in message.content.split(",")]
            goal["commands"] = commands

        return {'messages': messages, 'goals': state['goals']}


    def identify_goals(self, state: AgentState):
        system_instructions = get_instructions("identify_goals", document=self.doc)
        messages = state['messages']
        messages = [SystemMessage(content=system_instructions)] + messages
        messages +=[HumanMessage(content="What are my goals for this document?")]
        message = self.model.invoke(messages)
        messages.append(message)
        new_state = {'messages': messages, 'goals': json.loads(message.content)["goals"]}
        return new_state
