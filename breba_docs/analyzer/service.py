import json

from breba_docs.services.agent import Agent
from breba_docs.socket_server.client import Client


def get_input_message(agent: Agent, text: str):
    instruction = agent.provide_input(text)
    if instruction == "breba-noop":
        return None
    elif instruction:
        return json.dumps({"input": instruction})


def collect_response(response: str, command_executor: Client, agent: Agent):
    """
    Collect a response from the command executor and any additional responses that come back based on if the AI
    thinks that the command is waiting for input or not. If AI thinks it is waiting for input, then we send in the
    input and await the additional response. If AI does not think it is waiting for input, we just return the
    response.

    Args:
        response (str): The initial response from the command executor.
        command_executor (Client): The client to send messages to and receive responses from.
        agent (Agent): The AI agent to ask if the command is waiting for input or not.

    Returns:
        str: The full response including any additional responses due to input.
    """
    if response:
        input_message = get_input_message(agent, response)
        input_response = ""
        if input_message:
            input_response = command_executor.send_message(input_message)
        # TODO: This additional response covers for cases where at the first attempt the response comes back empty
        #  Due to a timeout. But really it is just a slow executing command and this works as backup
        #  Should probably introduce a max wait time and loop over at some interval to double check response
        additional_response = collect_response(command_executor.read_response(), command_executor, agent)
        return response + input_response + additional_response

    return ''


def execute_command_and_collect_response(command, command_executor: Client, agent: Agent):
    # when response comes back we want to check if AI thinks it is waiting for input.
    # if it is, then we send in input
    # if it is not, we keep reading the response
    response = command_executor.send_message(json.dumps(command))
    response = collect_response(response, command_executor, agent)

    return response


def analyze(agent: Agent, doc: str):
    commands = agent.fetch_commands(doc)
    with Client() as commands_client:
        for command in commands:
            command = {"command": command}
            response = execute_command_and_collect_response(command, commands_client, agent)
            agent_output = agent.analyze_output(response)
            print(agent_output)
