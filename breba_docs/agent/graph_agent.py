import json
from dataclasses import asdict
from typing import TypedDict, Literal

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from breba_docs.agent.agent import Agent
from breba_docs.agent.instruction_reader import get_instructions
from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.services.command_executor import ContainerCommandExecutor, LocalCommandExecutor
from breba_docs.services.document import Document
from breba_docs.services.reports import GoalReport, CommandReport, Goal


class AgentState(TypedDict):
    messages: list[AnyMessage]
    goals: list[Goal]
    goal_reports: list[GoalReport]
    current_goal: Goal | None
    goal_evaluation_count: int | None


# TODO: test this class by testing individual functions on input state and output state
# TODO: maybe unit test entire graph somehow
class GraphAgent:

    def __init__(self, doc: Document):
        self.agent: Agent = OpenAIAgent()
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.doc = doc

        self.system_instructions = None
        graph = StateGraph(AgentState)
        graph.add_node("identify_goals", self.identify_goals)
        graph.add_node("start_next_goal", self.start_next_goal)
        graph.add_node("identify_commands", self.identify_commands)
        graph.add_node("execute_commands", self.execute_commands)
        graph.add_node("execute_mutator_commands", self.execute_mutator_commands)

        graph.set_entry_point("identify_goals")
        graph.add_edge("identify_goals", "start_next_goal")
        graph.add_conditional_edges("start_next_goal",
                                    self.process_more_goals,
                                    {True: "identify_commands", False: END})
        graph.add_edge("identify_commands", "execute_commands")

        # TODO: see if this can use a path map without having 3 paths
        graph.add_conditional_edges("execute_commands",
                                    self.commands_succeeded,
                                    {True: "start_next_goal", False: "execute_mutator_commands"})

        graph.add_conditional_edges(
            "execute_mutator_commands",
            self.should_reevaluate_goal,
            {True: "identify_commands", False: "start_next_goal"}
        )

        self.graph = graph.compile()

    def invoke(self):
        return self.graph.invoke({"messages": [], "goals": [], "goal_reports": []})

    def should_reevaluate_goal(self, state: AgentState):
        # TODO: log every step of the graph
        # By convention, we are always working on the last goal report
        current_goal_report: GoalReport = state['goal_reports'][-1]
        if state['goal_evaluation_count'] >= 4:
            return False
        # TODO: currently the way to tell if doc has changed and needs to be reevaluated for the given goal
        #  is to see if any of the modify commands succeeded. In future should engineer smarter way
        return any(modify_command_report.success for modify_command_report in current_goal_report.modify_command_reports)

    def commands_succeeded(self, state: AgentState) -> Literal["identify_commands", "execute_mutator_commands"] | END:
        current_goal = state['goal_reports'][-1]
        return all(command_report.success for command_report in current_goal.command_reports)

    def process_more_goals(self, state: AgentState):
        return state['current_goal'] is not None


    def _get_command_reports(self, commands: list[str]) -> list[CommandReport]:
        modify_commands_reports = []
        with LocalCommandExecutor.session(self.agent) as session:
            for command in commands:
                command_output = session.execute_command(command)
                command_report = self.agent.analyze_output(command_output)
                modify_commands_reports.append(command_report)
        return modify_commands_reports

    # Use cases:
    #   If mutator commands made changes, then re-evaluate goal
    #   If no mutator commands could not succeed after retries, then we update report with Error and move to next goal
    #   If mutator commands made no changes or failed, then we want to refine the commands to fix them (retry count)
    def execute_mutator_commands(self, state: AgentState):
        current_goal = state['goal_reports'].pop()
        for command_report in current_goal.command_reports:
            if not command_report.success:
                modify_commands = self.agent.fetch_modify_file_commands(self.doc.filepath, command_report)
                command_reports = self._get_command_reports(modify_commands)
                current_goal.modify_command_reports += command_reports
        return {'goal_reports': state['goal_reports'] + [current_goal]}

    def execute_commands(self, state: AgentState):
        # Grab the commands from the last goal report
        current_goal = state["goal_reports"].pop()
        commands: list[str] = [command_report.command for command_report in current_goal.command_reports]

        command_reports = []
        # TODO: ContainerCommandExecutor needs to take an interface that provides input to prompts
        with ContainerCommandExecutor.executor_and_new_container(self.agent) as executor:
            with executor.session() as session:
                for command in commands:
                    response = session.execute_command(command)
                    command_report = self.agent.analyze_output(response)
                    command_reports.append(command_report)

        current_goal.command_reports = command_reports

        return { 'goal_reports': state['goal_reports'] + [current_goal] }

    def start_next_goal(self, state: AgentState):
        try:
            current_goal = state['goals'].pop(0)
        except IndexError:
            current_goal = None
        return {'current_goal': current_goal, 'goals': state['goals'], 'goal_evaluation_count': 0}

    def identify_commands(self, state: AgentState):
        current_goal: Goal = state['current_goal']
        system_instructions = get_instructions("fetch_commands", document=self.doc.reload().content)

        # Remove old messages from the state because each goal will have an own clean slate
        messages = [SystemMessage(content=system_instructions)]

        message = HumanMessage(content=f"Give me commands for this goal: {json.dumps(asdict(current_goal))}")
        messages += [message]
        model_response = self.model.invoke(messages)
        messages.append(model_response)
        commands = [cmd.strip() for cmd in model_response.content.split(",")]

        command_reports = [CommandReport(command, None, None, None) for command in commands]
        goal_report = GoalReport(current_goal, command_reports)

        return {
            'goals': state['goals'],  # Remove processed goal
            'messages': messages,
            'goal_reports': state['goal_reports'] + [goal_report],
            'goal_evaluation_count': state['goal_evaluation_count'] + 1
        }

    def identify_goals(self, state: AgentState):
        system_instructions = get_instructions("identify_goals", document=self.doc.content)

        # Build new messages list
        new_messages: list[AnyMessage] = [SystemMessage(content=system_instructions)] + state['messages']
        new_messages.append(HumanMessage(content="What are my goals for this document?"))

        # Invoke the model
        response_message = self.model.invoke(new_messages)
        new_messages.append(response_message)

        # Parse goals from the response
        new_goals = [Goal(**goal) for goal in json.loads(response_message.content)["goals"]]

        return { 'messages': new_messages, 'goals': new_goals }

