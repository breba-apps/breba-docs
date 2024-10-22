import json

from openai import OpenAI

from breba_docs.services.agent import Agent
from breba_docs.services.output_analyzer_result import CommandReport


class OpenAIAgent(Agent):
    INSTRUCTIONS_GENERAL = """
You are assisting a software program to validate contents of a document.
"""

    INSTRUCTIONS_ANALYZE_OUTPUT = f"""
You are assisting a software program to validate contents of a document. After running commands from the
documentation, the user received some output and needs help understanding the output. 
Here are important instructions:
0) Never return markdown. You will respond with JSON without special formatting
1) The user will present you with output of the commands that were just run.
2) The command has failed if there are errors and the user did not achieve intended goal
3) You will respond with a json that looks like this:
{CommandReport.example_str()}
"""

    INSTRUCTIONS_RESPONSE = """
You are assisting a software program to run commands. Given a programs output you will need to provide a response.
Here are important instructions:
0) You will provide an exact response if response is actually expected. This will be passed directly to the program.
1) You will respond with "breba-noop" if response is not expected
"""

    INSTRUCTIONS_GET_COMMANDS_FOR_TASK = """
You are an expert in Quality Control for documentation. You are 
assisting a software program to create a list of terminal commands that will accomplish a given task.
Important: Never return markdown. You will return text without special formatting.
Important: The user is usually expecting a list of commands that will be run in the terminal sequentially. 

{}
"""

    INSTRUCTIONS_GET_GOALS = """
You are an expert in Quality Control for documentation. You  are assisting a software 
program to check that the tasks described in the following document actually work. NEVER USE MARKDOWN. JUST
PROVIDE JSON THAT CAN BE USED IN A SOFTWARE PROGRAM.

Respond using json like:
{
  "goals": [
    {
      "name": "getting started",
      "description": "As a user I would like to get started with the software"
    }
  ]
}
"""

    def __init__(self):
        self.client = OpenAI()
        self.assistant = self.client.beta.assistants.create(
            name="Breba Docs",
            instructions=OpenAIAgent.INSTRUCTIONS_GENERAL,
            model="gpt-4o-mini"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def do_run(self, message, instructions):
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
            instructions=instructions
        )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )

            return messages.data[0].content[0].text.value
        else:
            print(f"OpenAI run.status: {run.status}")

    def fetch_goals(self, doc: str) -> list[dict]:
        message = ("Provide a list of goals that a user can accomplish via a terminal based on "
                   "the documentation. Headings and titles can be used as an indicator of a task. \n")
        assistant_output = self.do_run(message, OpenAIAgent.INSTRUCTIONS_GET_GOALS + doc)
        # TODO: create class for Goal that will parse the string using json.loads
        assistant_output = json.loads(assistant_output)
        return assistant_output["goals"]

    def fetch_commands(self, doc: str, goal: str) -> list[str]:
        message = goal + "\n"
        message += (
            """Provide a list of terminal commands that accomplish the task. This is a broad definition of 
the task. Make sure to list all commands needed to accomplish this task. I am a software program that will 
run these commands on a system that has little installed other than python. Do not assume any software is 
installed. Only use the commands from the document exactly as they are written in the document. Do not modify 
commands from the document. Do not invent new commands. Respond using a comma separated list. If there are no 
commands listed in the document support completing this task, return an empty list.""")
        assistant_output = self.do_run(message, OpenAIAgent.INSTRUCTIONS_GET_COMMANDS_FOR_TASK.format(doc))
        return [cmd.strip() for cmd in assistant_output.split(",")]

    def analyze_output(self, text: str) -> CommandReport:
        message = "Here is the output after running the commands. What is your conclusion? \n"
        message += text
        return CommandReport.from_string(self.do_run(message, OpenAIAgent.INSTRUCTIONS_ANALYZE_OUTPUT))

    def provide_input(self, text: str) -> str:
        message = ("Here is the output after running the commands. "
                   "If the program is expecting input, what should it be?\n")
        message += text
        run_result = self.do_run(message, OpenAIAgent.INSTRUCTIONS_RESPONSE)
        return run_result

    def close(self):
        self.client.beta.assistants.delete(self.assistant.id)
