import json

from breba_docs.services.agent import Agent
from breba_docs.socket_server.client import Client


def accumulate_response(command, command_executor: Client, agent: Agent):
    # when response comes back we want to check if AI thinks it is waiting for input.
    # if it is, then we send in input
    # if it is not, we keep reading the response
    response = ""
    # TODO: This is bogus because providing input is dependent on retries
    retries = 1
    while retries > 0:
        if command:
            new_response = command_executor.send_message(json.dumps(command))
            response += new_response
        else:
            retries -= 1  # if we don't have a command, we don't want to keep monitoring for new responses forever
            new_response = command_executor.read_response(2)
            response += new_response

        if new_response:
            instruction = agent.provide_input(new_response)
            if instruction == "breba-noop":
                command = None
            elif instruction:
                command = {"input": instruction}
        else:
            command = None

    return response


def analyze(agent: Agent, doc: str):
    commands = agent.fetch_commands(doc)
    commands_client = Client()
    response = ""
    with commands_client:
        for command in commands:
            command = {"command": command}
            response = accumulate_response(command, commands_client, agent)
            agent_output = agent.analyze_output(response)
            print(agent_output)
