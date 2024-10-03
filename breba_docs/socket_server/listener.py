import asyncio
import json
from asyncio import StreamReader, StreamWriter

import pexpect
import uuid

PORT = 44440


async def collect_output(process, writer: StreamWriter, end_marker: str):
    while True:
        try:
            output = process.read_nonblocking(1024, timeout=1)
            if output == end_marker:
                break
            else:
                print(output.strip())
                writer.write(output.strip().encode())
                await writer.drain()
        except pexpect.exceptions.TIMEOUT:
            # TODO: maybe send something to keep the connection alive, since we are now breaking on end_marker
            await asyncio.sleep(0.1)
        except pexpect.exceptions.EOF as e:
            print("End of process output.")
            break


def handle_command(command, process, writer: StreamWriter):
    if command:
        command_end_marker = f"Completed {str(uuid.uuid4())}"
        command = f"{command} && echo {command_end_marker}"
        process.sendline(command)

        # start executing collect_output, but pass control back to caller in order to
        # handle additional commands/inputs
        task = asyncio.create_task(collect_output(process, writer, command_end_marker))
        return task


async def handle_client(reader: StreamReader, writer: StreamWriter, process, server):
    client_address = writer.get_extra_info('peername')
    print(f"Connection from {client_address}")

    output_tasks = []
    while True:
        data = await reader.read(1024)
        if not data:
            break

        data = json.loads(data.decode().strip())

        command = data.get("command")
        if command == "quit":
            print("Quit command received, closing connection.")
            writer.write("Quit command received, closing connection.".encode())
            break
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

    server.close()
    await server.wait_closed()
    print("Server Closed")


async def start_server(process):
    server = await asyncio.start_server(
        lambda reader, writer: handle_client(reader, writer, process, server), '0.0.0.0', PORT
    )
    print(f"Server listening on 0.0.0.0:{PORT}")
    async with server:
        await server.serve_forever()
    print("Serving is done")


async def run():
    process = pexpect.spawn('/bin/bash', encoding='utf-8', env={"PS1": ""})

    try:
        await asyncio.create_task(start_server(process))
    except asyncio.CancelledError:
        print("Server shutdown detected. Cleaning up...")


if __name__ == "__main__":
    asyncio.run(run())
