import json

from breba_docs.services.agent import Agent
from breba_docs.socket_server.client import Client


def analyze(agent: Agent, doc: str):
    commands = agent.fetch_commands(doc)
    commands_client = Client()
    response = ""
    with commands_client:
        for command in commands:
            command = {"command": command}
            response = commands_client.send_message(json.dumps(command))
    print(agent.analyze_output(response))



