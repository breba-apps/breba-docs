# First we initialize the model we want to use.
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from breba_docs.agent.instruction_reader import get_instructions
from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.services.reports import CommandReport


class CommandAgent:
    def __init__(self, executor):
        self.executor: ContainerCommandExecutor = executor
        self.model = ChatOpenAI(model="gpt-4o", temperature=0)
        self.graph = create_react_agent(self.model, tools=[self._create_execute_command_tool()])

    def _create_execute_command_tool(self):
        @tool
        def execute_command(command: str) -> str:
            """Use this to run any command in the terminal"""
            return self.executor.execute_command(command)

        return execute_command

    @staticmethod
    def print_stream(stream):
        for s in stream:
            message = s["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                message.pretty_print()

    def invoke(self, command: str):
        instructions = get_instructions("reactive_analyze_output", example_report=CommandReport.example_str())
        inputs = {"messages": [
            ("system", instructions),
            ("user", command),
        ]}
        result = self.graph.invoke(inputs, {"recursion_limit": 100})
        return result


if __name__ == "__main__":
    load_dotenv()

    commands = ['python3 -m venv .venv', 'cd .venv',
                    'source bin/activote']
    with ContainerCommandExecutor.executor_and_new_container(OpenAIAgent()) as command_executor:
        with command_executor.session() as session:
            agent = CommandAgent(session)
            for command in commands:
                messages = agent.invoke(command)["messages"]
                for message in messages:
                    if isinstance(message, tuple):
                        print(message)
                    else:
                        message.pretty_print()
