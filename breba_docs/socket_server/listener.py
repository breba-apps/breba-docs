import asyncio
import json
import shlex
import logging
from asyncio import StreamReader, StreamWriter

import pexpect

PORT = 44440
server: asyncio.Server | None = None

logger = logging.getLogger(__name__)


# TODO rename to stream_output
async def collect_output(process, writer: StreamWriter, end_marker: str):
    while True:
        try:
            output = process.read_nonblocking(1024, timeout=1)
            logger.info(output.strip())
            # TODO: handle unexpected exceptions gracefully. Currently client doesn't receive anything in case of
            #  unexpected error and may be stuck waiting for response indefinitely. The client could implement a timeout,
            #  it would save some time to know that things went badly
            writer.write(output.encode())
            await writer.drain()
            if end_marker in output:
                logger.info("Breaking on end marker")
                break
        except pexpect.exceptions.TIMEOUT:
            await asyncio.sleep(0.1)
        except pexpect.exceptions.EOF as e:
            logger.info("End of process output.")
            break
        except Exception as e:
            logger.exception(e)
            break

async def command_scheduler_loop(commands_queue: asyncio.Queue, process, writer: StreamWriter):
    while True:
        command = await commands_queue.get()
        await handle_command(command, process, writer)
        await asyncio.sleep(0.1)

def command_end_marker(command_id):
    return f"Completed {command_id}"

async def handle_command(command: dict, process, writer: StreamWriter):
    logger.info(f"command: {command}")
    if command:
        command_text = command.get("command")
        command_id = command.get("command_id")
        # basically echo the command, but have to escape quotes first
        escaped_command = shlex.quote(command_text)
        echo_text = f"echo $ {escaped_command}\n"
        process.sendline(echo_text)
        logger.info(f"Sending to process echo: {echo_text}")

        end_marker = command_end_marker(command_id)
        command = f"{command_text} && echo {end_marker}"
        process.sendline(command)
        logger.info(f"Sending to process command: {command}")

        # TODO: when collect_output is stuck waiting for input, but input never comes, then this never returns and
        #  new commands that are put on the queue are never picked up since the loop is waiting for this to return
        await collect_output(process, writer, end_marker)


async def stop_server():
    server.close()
    await server.wait_closed()
    logger.info("Server Closed")


async def handle_client(reader: StreamReader, writer: StreamWriter):
    client_address = writer.get_extra_info('peername')
    logger.info(f"Connection from {client_address}")

    process = pexpect.spawn('/bin/bash', encoding='utf-8', env={"PS1": ""}, echo=False)
    process.sendline('. .venv/bin/activate')

    commands_queue = asyncio.Queue()
    command_scheduler_task = asyncio.create_task(command_scheduler_loop(commands_queue, process, writer))
    while True:
        data = await reader.read(1024)
        if not data:
            break

        data = json.loads(data.decode().strip())
        command = data.get("command")
        if command == "quit":
            logger.info("Quit command received, closing connection.")
            writer.write("Quit command received, closing connection.".encode())
            await stop_server()  # First stop the server
            break  # then break out of the loop to close the connection
        elif command:
            await commands_queue.put(data)

        input_text = data.get("input")

        # TODO: race condition. If input is received, but no other commands were sent AND the client receive timeout
        #   Elapsed, then the client will not receive any additional output from the input instruction and all the
        #   consequences
        if input_text:
            # TODO: write to client the input, because in terminal when you type text to respond to a prompt,
            #  the text shows up after the prompt. Simply sending it to process does not do that
            logger.info(f"Sending to process input: {input_text}")
            process.sendline(input_text)

    if command_scheduler_task:
        command_scheduler_task.cancel()

    # TODO: this may be an issue because when the server is closed on quit doesn't actually get here
    writer.write("Closing writer...".encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def start_server():
    global server
    server = await asyncio.start_server(
        lambda reader, writer: handle_client(reader, writer), '0.0.0.0', PORT
    )
    logger.info(f"Server listening on 0.0.0.0:{PORT}")
    async with server:
        await server.serve_forever()
    logger.info("Serving is done")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("server.log"),  # Log to file
            logging.StreamHandler()  # Log to console
        ]
    )
    asyncio.run(start_server())
