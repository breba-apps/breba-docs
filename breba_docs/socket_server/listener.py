import asyncio
import json
from asyncio import StreamReader, StreamWriter

import pexpect

PORT = 44440


async def handle_client(reader: StreamReader, writer: StreamWriter, process, server):
    client_address = writer.get_extra_info('peername')
    print(f"Connection from {client_address}")

    # This will start executing the task. We will await it at the end to make sure that it has finished
    output_task = asyncio.create_task(read_output(process, writer))

    while True:
        data = await reader.read(1024)
        if not data:
            break

        data = json.loads(data.decode().strip())

        command = data.get("command")
        input_text = data.get("input")

        if command == "quit":
            print("Quit command received, closing connection.")
            break

        if command:
            process.sendline(command)

        # Handle further input if expected
        if input_text:
            process.sendline(input_text)

    output_task.cancel()

    writer.write("Server Closed".encode())
    await writer.drain()


    writer.close()
    await writer.wait_closed()

    server.close()
    await server.wait_closed()
    print("Server Closed")


async def read_output(process, writer: StreamWriter):
    while True:
        try:
            output = process.read_nonblocking(1024, timeout=1)
            if output:
                print(output.strip())
                writer.write(output.strip().encode())
                await writer.drain()
        except pexpect.exceptions.TIMEOUT:
            await asyncio.sleep(0.1)
        except pexpect.exceptions.EOF as e:
            print("End of process output.")
            break


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
