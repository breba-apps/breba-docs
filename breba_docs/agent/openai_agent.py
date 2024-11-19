import json
import os
from pathlib import Path

from openai import OpenAI

from breba_docs.agent.agent import Agent
from breba_docs.services.reports import CommandReport


class OpenAIAgent(Agent):
    INSTRUCTIONS_GENERAL = """
You are assisting a software program to validate contents of a document.
"""

    INSTRUCTIONS_GET_COMMANDS_FOR_TASK = """
You are an expert in Quality Control for documentation. You are 
assisting a software program to create a list of terminal commands that will accomplish a given task.
Important: Never return markdown. You will return text without special formatting.
Important: The user is usually expecting a list of commands that will be run in the terminal sequentially. 
Important: When reading the document, you will only use terminal commands in the document exactly as they are written 
    in the document even if there are typos or errors.
Important: Do not use commands that are not in the document, unless asked to do so explicitly 
Important: Goal and task are used interchangeably.


{}
"""

    INSTRUCTIONS_GET_GOALS = """
You are an expert in Quality Control for documentation. You  are assisting a software 
program to check that the tasks described in the following document actually work. NEVER USE MARKDOWN. JUST
PROVIDE JSON THAT CAN BE USED IN A SOFTWARE PROGRAM. The goals should be high level tasks that a user would want
to achieve. You need to come up with as few goals as possible, but still cover all the commands listed the document

Respond using json like:
{
  "goals": [
    {
      "name": "getting started",
      "description": "As a user I would like to get started with the software"
    }
  ]
}


Do not just make up sub goals. For example, if the documentation has instructions for Getting Started but splits that
 into multiple steps, it is still a single goal of "getting started". Do not split the goal into sub goals of 
 "install the software", and "run the software". For example, the below document would have only one goal of 
 "getting started":

## Getting Started

Install the software using the following commands

```bash
  pip install mysoftware
```

Then run the software using these commands:
```
   mysoftware run
```

"""

    INSTRUCTIONS_FETCH_MODIFY_FILE_COMMANDS = """
You are an expert in Quality Control for documentation. You are 
assisting a software program to correct issues in the documentation.

IMPORTANT: NEVER RETURN MARKDOWN. YOU WILL RETURN TEXT WITHOUT SPECIAL FORMATTING. 
Important: Return only the commands to run because your response will be used by a software program to run these
   commands in the terminal.

You will respond with a json list that contains a field called "commands". 

When generating commands to modify the file, change the entire line in the file. Do not simply replace one word.


Here is the document:
{}
"""

    INPUT_FIRST_COMMAND_SYSTEM_INSTRUCTION = """
You are assisting a software program to run commands. We are trying to determine if 
the command is stuck waiting for user input. The goal is to answer all the prompts so that the command can finish 
executing.

You will answer with minimal text and not use formatting or markdown.
"""

    INPUT_FIRST_MESSAGE = """
    Does the last sentence in the command output contain a prompt asking the user for input in order to complete the command execution? 
    Answer with "Yes" if the last thing in the command output is a prompt asking the user for some input.
    Answer with "No" if the last thing in the command output is not a user prompt:
    
    Important: If there is additional text after the user prompt, that means the prompt was answered your answer must be "No"
    """

    INPUT_FIRST_MESSAGE_VERIFY = """
    Is the user prompt the last sentence of the command output? Answer only with "Yes" or "No"
    """

    INPUT_FOLLOW_UP_COMMAND_INSTRUCTION = """You need to come up with the right answer to this prompt. To the best of your 
abilities what should be put into the terminal to continue executing this command? 
Reply with exact response that will go into the terminal.

You will answer with minimal text and not use formatting or markdown.
"""

    INPUT_FOLLOW_UP_MESSAGE = """What should the response in the terminal be? Provide the exact answer to put into the
    terminal in order to answer the prompt."""

    def __init__(self):
        self.client = OpenAI()
        self.assistant = self.client.beta.assistants.create(
            name="Breba Docs",
            instructions=OpenAIAgent.INSTRUCTIONS_GENERAL,
            model="gpt-4o-mini"
        )
        self.thread = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_last_message(self):
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id
        )

        return messages.data[0].content[0].text.value

    def do_run(self, message, instructions, new_thread=True):
        print(f"Message: {message}")
        print(f"Instructions: {instructions}")

        # openAI max size of request is 256000, so we need to truncate the first part of the message
        # in order to allow for the request to be below 256K characters.
        max_length = 250000
        truncated_message = message[-max_length:]

        if new_thread:
            self.thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=truncated_message
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=instructions,
            temperature=0.0,
            top_p=1.0,
        )

        if run.status == 'completed':
            agent_response = self.get_last_message()
            print(f"Agent Response: {agent_response}")
            return agent_response
        else:
            print(f"OpenAI run.status: {run.status}")

    def fetch_goals(self, doc: str) -> list[dict]:
        message = ("Provide a list of goals that a user can accomplish via a terminal based on "
                   "the documentation. Headings and titles can be used as an indicator of a task. \n")
        assistant_output = self.do_run(message, OpenAIAgent.INSTRUCTIONS_GET_GOALS + doc)
        # TODO: create class for Goal that will parse the string using json.loads
        assistant_output = json.loads(assistant_output)
        return assistant_output["goals"]

    def fetch_commands(self, doc: str, goal: dict) -> list[str]:
        # TODO: When extracting commands, make sure that these commands are for the specific goal
        # TODO: use json instead of csv
        # TODO: test for returning an empty list
        message = json.dumps(goal) + "\n"
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
        instructions = get_instructions("analyze_output", example_report=CommandReport.example_str())
        message = "Here is the output after running the commands. What is your conclusion? \n"
        message += text
        analysis = self.do_run(message, instructions)
        return CommandReport.from_string(analysis)

    def provide_input(self, text: str) -> str:
        message = OpenAIAgent.INPUT_FIRST_MESSAGE + "\n" + text
        has_prompt = self.do_run(message, OpenAIAgent.INPUT_FIRST_COMMAND_SYSTEM_INSTRUCTION)
        if has_prompt == "Yes":
            prompt_verified = self.do_run(OpenAIAgent.INPUT_FIRST_MESSAGE_VERIFY,
                                          OpenAIAgent.INPUT_FIRST_COMMAND_SYSTEM_INSTRUCTION,
                                          False)
            if prompt_verified == "Yes":
                prompt_answer = self.do_run(OpenAIAgent.INPUT_FOLLOW_UP_MESSAGE,
                                            OpenAIAgent.INPUT_FOLLOW_UP_COMMAND_INSTRUCTION,
                                            False)
                return prompt_answer
        return "breba-noop"

    def fetch_modify_file_commands(self, filepath: Path, command_report: CommandReport) -> list[str]:
        message = f"I have this output from trying to accomplish my goal:\n {command_report.insights}\n"
        message += f"This is the command that was executed:\n {command_report.command}\n"
        message += f"Here is the file:\n {filepath}\n"
        message += f"Can you write a sed command to fix this issue in the file?"
        print("WORKING DIR: ", os.getcwd())
        with open(filepath, "r") as f:
            document = f.read()
            instructions = OpenAIAgent.INSTRUCTIONS_FETCH_MODIFY_FILE_COMMANDS.format(document)
            raw_response = self.do_run(message, instructions)
            commands = json.loads(raw_response)["commands"]  # should be a list. TODO: validate?

        return commands

    def close(self):
        self.client.beta.assistants.delete(self.assistant.id)


def get_instructions(name, **kwargs):
    filepath = Path(__file__).parent / "instructions" / f"{name}.txt"
    with open(filepath) as file:
        return file.read().format(**kwargs)