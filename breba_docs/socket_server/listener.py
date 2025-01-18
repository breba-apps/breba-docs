import asyncio
import json
import shlex
import logging
from asyncio import StreamReader, StreamWriter

from interactive_process import InteractiveProcess, TerminatedProcessError, ReadWriteError

PORT = 44440
server: asyncio.Server | None = None

logger = logging.getLogger(__name__)


async def stream_output(process: InteractiveProcess, writer: StreamWriter, end_marker: str):
    while True:
        try:
            output = process.read_nonblocking(timeout=1)
            if output:
                logger.info("Process output: " + output.strip())
                writer.write(output.encode())
                await writer.drain()
            if end_marker in output:
                logger.info("Breaking on end marker")
                break
        except TimeoutError:
            # TODO: this will be an infinite loop if end_marker is not found due to an error in the command, should use max_timeout, or use an http client
            await asyncio.sleep(0.1)  # TODO: maybe add max sleep time.
        except (TerminatedProcessError, ReadWriteError) as e:
            logger.info("End of process output.")
            logger.info(e)
            break
        except Exception as e:
            logger.exception(e)
            break

async def command_scheduler_loop(commands_queue: asyncio.Queue, process, writer: StreamWriter):
    while True:
        command = await commands_queue.get()
        await handle_command(command, process, writer)

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
        process.send_command(echo_text)
        logger.info(f"Sending to process echo: {echo_text}")

        end_marker = command_end_marker(command_id)
        command = f"{command_text} && echo {end_marker}"
        process.send_command(command)
        logger.info(f"Sending to process command: {command}")

        # TODO: when stream_output is stuck waiting for input, but input never comes, then this never returns and
        #  new commands that are put on the queue are never picked up since the loop is waiting for this to return
        await stream_output(process, writer, end_marker)


async def stop_server():
    server.close()
    await server.wait_closed()
    logger.info("Server Closed")

def create_on_error(writer):
    def on_error(error):
        writer.write(f"Error: {error}".encode())
    return on_error

async def read_message(reader: StreamReader) -> str:
    prefix = await reader.readexactly(4)
    length = int.from_bytes(prefix)  # assume default is "big"

    return (await reader.readexactly(length)).decode()


async def handle_client(reader: StreamReader, writer: StreamWriter):
    client_address = writer.get_extra_info('peername')
    logger.info(f"Connection from {client_address}")

    process = InteractiveProcess()
    process.send_command('. .venv/bin/activate')

    commands_queue = asyncio.Queue()
    command_scheduler_task = asyncio.create_task(command_scheduler_loop(commands_queue, process, writer))
    while True:
        # TODO: test these error conditions
        try:
            message = await read_message(reader)
        except asyncio.IncompleteReadError:
            logging.error("Client disconnected prematurely. Will not handle partial data.")
            break
        except ConnectionResetError:
            logging.error("Connection reset by client. Client disconnected.")
            break
        if not message:
            break

        try:
            data = json.loads(message.strip())
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
                process.send_command(input_text)
        except json.JSONDecodeError:
            writer.write(b"Error: Invalid JSON data received from client. Received: " + message.encode())

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
