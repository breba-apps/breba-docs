from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

load_dotenv()

llm = ChatOpenAI(model="gpt-4o")


class State(MessagesState):
    topic: str
    answer: str


@tool
def refine_prompt(prompt: str):
    """Improves the prompt
    Args:
        prompt (str): original user prompt
    """
    print("Tool calling:")
    llm_response = llm.invoke(
        [
            {"role": "user", "content": f"Improve the following prompt make sure the prompt includes number of "
                                        f"words to generate. The number of words should not exceed 50: {prompt}"}
        ]
    )
    return llm_response


tools = [refine_prompt]
tool_node = ToolNode(tools)
llm_with_tools = llm.bind_tools(tools)


def refine_topic(state: State):
    llm_response = llm_with_tools.invoke(
        [
            {"role": "system", "content": f"Improve the prompt by using refine_prompt tool. Use the exact user prompt as input parameter to the tool."},
            {"role": "user", "content": f"general relativity and gravity"}
        ]
    )
    return {"topic": llm_response.content, "messages": [llm_response]}

def generate_answer(state: State):
    print("\nGenerating answer")
    llm_response = llm.invoke(
        [
            {"role": "user", "content": "provide answer in markdown format"},
            {"role": "user", "content": state["messages"][-1].content}
        ]
    )
    return {"answer": llm_response.content}


graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node("action", tool_node)
    .add_node(generate_answer)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "action")
    .add_edge("action", "generate_answer")
    .compile()
)

for message_chunk, metadata in graph.stream(
    {"topic": "ice cream"},
    stream_mode="messages",
):
    if message_chunk.content:
        print(message_chunk.content, end="", flush=True)