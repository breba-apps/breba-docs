from typing import TypedDict, Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from langgraph.types import Command

from breba_docs.agent.build_agent import BuildAgent
from breba_docs.agent.instruction_reader import get_instructions

members = ["prompt_builder", "validator", "submitter"]

options = members + ["FINISH"]

system_prompt = get_instructions("create_form_agent", members=members)


class Route(TypedDict):
    reason: str
    next: Literal[*options]


class State(MessagesState):
    next: str


class CreateFormAgent:

    def __init__(self):
        # Initialize model with tools
        self.model = ChatOpenAI(model="gpt-4o", temperature=0)

        self.prompt_builder = BuildAgent()

        builder = StateGraph(State)
        builder.add_node("supervisor", self.supervisor_node)
        builder.add_node("prompt_builder", self.builder_node)
        builder.add_node("validator", self.validator_node)
        builder.add_node("submitter", self.submitter_node)
        builder.add_edge(START, "supervisor")

        self.graph = builder.compile()


    def supervisor_node(self, state: State) -> Command[Literal[*members, "__end__"]]:
        messages = [
                       {"role": "system", "content": system_prompt},
                   ] + state["messages"]
        response = self.model.with_structured_output(Route).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    def builder_node(self, state: State) -> Command[Literal["supervisor"]]:
        result = self.prompt_builder.invoke(state["messages"][-1].content)
        return Command(
            update={
                "messages": [
                    HumanMessage(content="The following message is from prompt_builder", name="prompt_builder"),
                    HumanMessage(content=result["prompt"], name="prompt_builder")
                ]
            },
            goto="supervisor"
        )

    def validator_node(self, state: State) -> Command[Literal["supervisor"]]:
        return Command(
            update={
                "messages": [
                    HumanMessage(content="Everything looks fine", name="validator")
                ]
            },
            goto="supervisor"
        )

    def submitter_node(self, state: State) -> Command[Literal["supervisor"]]:
        return Command(
            update={
                "messages": [
                    HumanMessage(content="Submitted everything", name="submitter")
                ]
            },
            goto="supervisor"
        )


    def visualize(self):
        with open("create_form_agent.png", "wb") as file:
            file.write(self.graph.get_graph().draw_mermaid_png())

    def stream(self, user_input: str):
        for event in self.graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            subgraphs=True
        ):
            print(event)

    def invoke(self, user_input: str):
        return self.graph.invoke({
            "messages": [ {"role": "user", "content": user_input}]
        },
    )


if __name__ == "__main__":
    load_dotenv()
    agent = CreateFormAgent()

    agent.stream(
        "We are creating a website for generating forms. You will need to produce HTML for a name, phone number, and a t-shirt size.")
