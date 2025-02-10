import abc

from breba_docs.agent.agent import Agent


class InputProvider(abc.ABC):
    @abc.abstractmethod
    def get_input(self, console_output: str) -> str:
        pass


class AgentInputProvider(InputProvider):
    def __init__(self, agent: Agent):
        self.agent = agent

    def get_input(self, console_output: str) -> str | None:
        instruction = self.agent.provide_input(console_output)
        if instruction == "breba-noop":
            return None
        elif instruction:
            return instruction
