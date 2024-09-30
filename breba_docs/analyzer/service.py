import shlex

from breba_docs.services.agent import Agent
from docker.models.containers import Container


def execute_detach(command, container):
    # this command will be able to run any command regardless of quote use
    docker_command = f"/bin/bash -c {shlex.quote(command.strip())}"

    exit_code, output = container.exec_run(
        docker_command,
        stdout=True,
        stderr=True,
        tty=True,
        stream=True,
    )

    return output


def execute_command(command, container):
    # this command will be able to run any command regardless of quote use
    docker_command = f"/bin/bash -c {shlex.quote(command.strip())}"

    exit_code, output = container.exec_run(
        docker_command,
        stdout=True,
        stderr=True,
        tty=True,
        stream=True,
    )

    output_text = ""

    for line in output:
        line_text = line.decode("utf-8")
        print(line_text.strip())
        output_text += line_text

    return output_text


def execute_commands_chained(commands, container):
    commands_with_echo = []

    for command in commands:
        command_echo = f"echo '{command}'"
        commands_with_echo.append(command_echo)  # first echo the command
        commands_with_echo.append(command)  # then run the command

    chained_commands = ' && '.join(commands_with_echo)

    print(f"Will run the following commands: {chained_commands}\n")

    output_text = execute_command(chained_commands, container)

    return output_text


def analyze(agent: Agent, container: Container, doc: str):
    commands = agent.fetch_commands(doc)
    output_text = execute_commands_chained(commands, container)
    print(agent.analyze_output(output_text))

    result = container.exec_run('ls -la')
    print(result.output.decode('utf-8'))

    container.stop()
    container.remove()


# keep this here for now
def analyze2(agent: Agent, container: Container, doc: str):
    commands = agent.fetch_commands(doc)
    output_text = ""
    for command in commands:
        print(f"Executing command: {command}")
        response = execute_command(command, container)
        output_text += response
    print(agent.analyze_output(output_text))

    result = container.exec_run('ls -la')
    print(result.output.decode('utf-8'))

    container.stop()
    container.remove()

