from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}

def generate_joke(state: State):
    llm_response = llm.invoke(
        [
            {"role": "user", "content": f"Generate 1500 words about general relativity and gravity"}
        ]
    )
    return {"joke": llm_response.content}


graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node(generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .compile()
)

for message_chunk, metadata in graph.stream(
    {"topic": "ice cream"},
    stream_mode="messages",
):
    if message_chunk.content:
        print(message_chunk.content, end="")