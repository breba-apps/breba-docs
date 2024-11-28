import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from breba_docs.agent.instruction_reader import get_instructions
from breba_docs.services.reports import GoalReport, CommandReport


class AgentState(TypedDict):
    messages: list[AnyMessage]
    goals: list[dict]
    goal_reports: list[GoalReport]


class GraphAgent:

    def __init__(self, doc: str):
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.doc = doc

        self.system_instructions = None
        graph = StateGraph(AgentState)
        graph.add_node("identify_goals", self.identify_goals)
        graph.add_node("identify_commands", self.identify_commands)

        graph.set_entry_point("identify_goals")
        graph.add_edge("identify_goals", "identify_commands")

        graph.add_conditional_edges(
            "identify_commands",
            self.process_more_goals,
            {True: "identify_commands", False: END}
        )

        self.graph = graph.compile()

    def invoke(self):
        return self.graph.invoke({"messages": [], "goals": [], "goal_reports": []})

    def process_more_goals(self, state: AgentState):
        return len(state['goals']) > 0

    def identify_commands(self, state: AgentState):
        current_goal = state['goals'][0]  # Assume safe access
        system_instructions = get_instructions("fetch_commands", document=self.doc)
        messages = [SystemMessage(content=system_instructions)]

        message = HumanMessage(content=f"Give me commands for this goal: {json.dumps(current_goal)}")
        messages += [message]
        model_response = self.model.invoke(messages)
        messages.append(model_response)
        commands = [cmd.strip() for cmd in model_response.content.split(",")]

        command_reports = [CommandReport(command, None, None) for command in commands]
        goal_report = GoalReport(current_goal["name"], current_goal["description"], command_reports)

        # Create a new state object
        new_state = {
            **state,
            'goals': state['goals'][1:],  # Remove processed goal
            'messages': messages,
            'goal_reports': state['goal_reports'] + [goal_report]
        }

        return new_state

    def identify_goals(self, state: AgentState) -> AgentState:
        # Get system instructions
        system_instructions = get_instructions("identify_goals", document=self.doc)

        # Build new messages list
        new_messages: list[AnyMessage] = [SystemMessage(content=system_instructions)] + state['messages']
        new_messages.append(HumanMessage(content="What are my goals for this document?"))

        # Invoke the model
        response_message = self.model.invoke(new_messages)
        new_messages.append(response_message)

        # Parse goals from the response
        new_goals = json.loads(response_message.content)["goals"]

        # Create a new state dictionary with updated values
        new_state: AgentState = {
            **state,
            'messages': new_messages,
            'goals': new_goals,
        }

        return new_state

