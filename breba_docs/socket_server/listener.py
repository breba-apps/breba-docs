import asyncio
import json
import shlex
from asyncio import StreamReader, StreamWriter

import pexpect
import uuid

PORT = 44440
server: asyncio.Server | None = None


async def collect_output(process, writer: StreamWriter, end_marker: str):
    while True:
        try:
            output = process.read_nonblocking(1024, timeout=1)
            print(f"Server Output: {output.strip()}")
            writer.write(output.encode())
            await writer.drain()
            if end_marker in output:
                print(f"Server Output: breaking on end marker")
                break
        except pexpect.exceptions.TIMEOUT:
            # TODO: maybe send something to keep the connection alive, since we are now breaking on end_marker
            await asyncio.sleep(0.1)
        except pexpect.exceptions.EOF as e:
            print("Server Output: End of process output.")
            break


def handle_command(command, process, writer: StreamWriter):
    if command:
        # basically echo the command, but have to escape quotes first
        escaped_command = shlex.quote(command)
        process.sendline(f"echo {escaped_command}\n")

        command_id = str(uuid.uuid4())
        command_end_marker = f"Completed {command_id}"
        command = f"{command} && echo {command_end_marker}"
        process.sendline(command)

        # start executing collect_output, but pass control back to caller in order to
        # handle additional commands/inputs
        task = asyncio.create_task(collect_output(process, writer, command_end_marker))
        return task


async def stop_server():
    server.close()
    await server.wait_closed()
    print("Server Closed")


async def handle_client(reader: StreamReader, writer: StreamWriter):
    client_address = writer.get_extra_info('peername')
    print(f"Server Output: Connection from {client_address}")

    process = pexpect.spawn('/bin/bash', encoding='utf-8', env={"PS1": ""}, echo=False)

    output_tasks = []
    while True:
        data = await reader.read(1024)
        if not data:
            break

        data = json.loads(data.decode().strip())

        command = data.get("command")
        if command == "quit":
            print("Server Output: Quit command received, closing connection.")
            writer.write("Quit command received, closing connection.".encode())
            await stop_server()  # First stop the server
            break  # then break out of the loop to close the connection
        else:
            output_tasks.append(handle_command(command, process, writer))

        input_text = data.get("input")

        # TODO: race condition. If input is received, but no other commands were sent AND the client receive timeout
        #   Elapsed, then the client will not receive any additional output from the input instruction and all the
        #   consequences
        if input_text:
            process.sendline(input_text)

    for task in output_tasks:
        # Check for None in case task has completed
        if task:
            task.cancel()

    writer.write("Server Closed".encode())
    await writer.drain()

    writer.close()
    await writer.wait_closed()


async def start_server():
    global server
    server = await asyncio.start_server(
        lambda reader, writer: handle_client(reader, writer), '0.0.0.0', PORT
    )
    print(f"Server Output: Server listening on 0.0.0.0:{PORT}")
    async with server:
        await server.serve_forever()
    print("Server Output: Serving is done")


if __name__ == "__main__":
    asyncio.run(start_server())
