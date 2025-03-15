from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from breba_docs.agent.instruction_reader import get_instructions


# Define the structure of our state
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

@tool
def ask_human(question: str) -> str:
    """Ask the human a question"""
    return input(question)

def should_call_tool(state: State) -> bool:
    if not state["messages"]:
        raise ValueError(f"State must contain messages: {state}")
    ai_message = state["messages"][-1]
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return True

    return False

class BuildAgent:

    def __init__(self):
        # Initialize the state
        self.initial_state: State = {"messages": []}

        # Initialize model with tools
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        self.model = model.bind_tools([ask_human])

        # Create a state graph
        graph = StateGraph(state_schema=State)
        tool_node = ToolNode(tools=[ask_human])

        # Add the agent and tools nodes
        graph.add_node("agent", self.agent)
        graph.add_node("tools", tool_node)

        # Define transitions: agent → tools, then loop back to agent
        graph.add_edge(START, "agent")
        graph.add_edge("tools", "agent")
        graph.add_conditional_edges("agent", should_call_tool, {True: "tools", False: END})

        self.graph = graph
        # Compile the state graph
        memory = MemorySaver()
        self.app = graph.compile(checkpointer=memory)


    def agent(self, state: State) -> State:
        response = self.model.invoke(state["messages"])
        HumanMessage(content="Hello")
        return {"messages": [response]}

    def visualize(self):
        with open("build_agent.png", "wb") as file:
            file.write(self.app.get_graph().draw_mermaid_png())

    def stream_graph_updates(self, user_input: str):
        config = {"configurable": {"thread_id": "1"}}
        for event in self.app.stream({
                "messages": [{"role": "system", "content": get_instructions("build_agent")},
                             {"role": "user", "content": user_input}]
            },
            config,
            stream_mode="values"
        ):
            event['messages'][-1].pretty_print()

    def invoke(self, user_input: str):
        return self.app.invoke({
                "messages": [{"role": "system", "content": get_instructions("build_agent")},
                             {"role": "user", "content": user_input}]
            },
            {"configurable": {"thread_id": "1"}}
        )


if __name__ == "__main__":
    load_dotenv()
    agent = BuildAgent()

    agent.stream_graph_updates("We are creating a website for generating forms. You will need to produce HTML for entering an email, a phone number and a t-shirt size.")
