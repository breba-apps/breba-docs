from typing import Generator

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.prebuilt import create_react_agent

from breba_docs.agent.instruction_reader import get_instructions


class GenerationAgent:

    def __init__(self):
        self.system_prompt = get_instructions("generation_agent")

        search_tool = TavilySearchResults(
            max_results=5,
            include_answer=True,
            include_raw_content=True,
            include_images=True,
        )

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.model = llm.bind_tools([search_tool])
        self.agent = create_react_agent(llm, tools=[search_tool])

    def stream(self, user_input: str) -> Generator[MessagesState, None, None]:
        inputs = {"messages": [
            ("system", self.system_prompt),
            ("user", user_input),
        ]}
        stream = self.agent.stream(inputs, stream_mode="values")
        for event in stream:
            yield event["messages"][-1]

    def invoke(self, user_input: str) -> MessagesState:
        inputs = {"messages": [
            ("system", self.system_prompt),
            ("user", user_input),
        ]}
        response = self.agent.invoke(inputs)
        return response


if __name__ == "__main__":
    load_dotenv()
    agent = GenerationAgent()

    agent_state = agent.invoke(
        "This website will show current weather for Stevens Pass. Use weather.gov and stevenspass.com for looking up information")
    agent_state["messages"][-1].pretty_print()
    # agent.stream( "This website will show current weather for Stevens Pass. Use weather.gov and stevenspass.com for looking up information")
