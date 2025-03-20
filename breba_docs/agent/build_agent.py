from typing import NotRequired

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState

from breba_docs.agent.instruction_reader import get_instructions


# Define the structure of our state
class State(MessagesState):
    prompt: NotRequired[str]


class BuildAgent:

    def __init__(self):
        self.system_prompt = get_instructions("build_agent")

        # Initialize model with tools
        self.model = ChatOpenAI(model="gpt-4o", temperature=0)

        # Create a state graph
        graph = StateGraph(state_schema=State)

        # Add the agent and tools nodes
        graph.add_node("agent", self.agent)
        graph.add_node("extract_prompt", self.extract_prompt)
        graph.add_node("get_user_input", self.get_user_input)

        # Define transitions: agent → tools, then loop back to agent
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", self.is_final_prompt, {True: "extract_prompt", False: "get_user_input"})
        graph.add_edge("get_user_input", "agent")
        graph.add_edge("extract_prompt", END)

        self.graph = graph
        self.app = graph.compile()

        self.final_state: State | None = None

    def is_final_prompt(self, state: State) -> bool:
        if len(state["messages"]) > 1:
            message = state["messages"][-1].content
            split_message = message.split("::final prompt result::")

            if len(split_message) > 1 and split_message[1]:
                return True
        return False

    def get_user_input(self, state: State) -> State:
        question = state["messages"][-1].content
        answer = input(question)
        return {"messages": [HumanMessage(content=answer)]}

    def extract_prompt(self, state: State) -> State:
        message = state["messages"][-1].content
        split_message = message.split("::final prompt result::")
        return {"prompt": split_message[1]}

    def agent(self, state: State) -> State:
        response = self.model.invoke(state["messages"])
        return {"messages": [response]}

    def visualize(self):
        with open("build_agent.png", "wb") as file:
            file.write(self.app.get_graph().draw_mermaid_png())

    def stream(self, user_input: str):
        for event in self.app.stream({
            "messages": [{"role": "system", "content": self.system_prompt},
                         {"role": "user", "content": user_input}]
        },
                stream_mode="values"
        ):
            event['messages'][-1].pretty_print()
            self.final_state = event

    def invoke(self, user_input: str):
        prompt = get_instructions("build_agent_user_prompt", prompt=user_input)
        return self.app.invoke({
            "messages": [{"role": "system", "content": self.system_prompt},
                         {"role": "user", "content": prompt}]
        }
        )


if __name__ == "__main__":
    load_dotenv()
    agent = BuildAgent()

    agent.stream(
        "We are creating a website for generating forms. You will need to produce HTML for entering an email, a phone number and a t-shirt size.")
    print(agent.final_state["prompt"])
