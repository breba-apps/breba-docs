from typing import NotRequired

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.prebuilt import create_react_agent

from breba_docs.agent.instruction_reader import get_instructions


# Define the structure of our state
class State(MessagesState):
    prompt: NotRequired[str]


@tool
def get_weather(location: str):
    """Gets current location of the user"""
    return "Hot and Sunny every day"


class GenerationAgent:

    def __init__(self):
        self.system_prompt = get_instructions("generation_agent")

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # tool = {"type": "web_search_preview"}
        # model = llm.bind_tools([tool])

        self.agent_executor = create_react_agent(llm, [get_weather])
        self.final_state = None

    def stream(self, user_input: str):
        for event in self.agent_executor.stream({
            "messages": [{"role": "system", "content": self.system_prompt},
                         {"role": "user", "content": user_input}]
        },
                stream_mode="values"
        ):
            event['messages'][-1].pretty_print()
            self.final_state = event

    def invoke(self, user_input: str) -> State:
        prompt = get_instructions("build_agent_user_prompt", prompt=user_input)
        return self.agent_executor.invoke({
            "messages": [{"role": "system", "content": self.system_prompt},
                         {"role": "user", "content": prompt}]
        })


if __name__ == "__main__":
    load_dotenv()
    agent = GenerationAgent()

    agent.stream(
        "This website will show weather forecast for Stevens Pass.")
    print(agent.final_state["prompt"])
