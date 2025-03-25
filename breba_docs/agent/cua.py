import subprocess
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
#  docker build -f cua.Dockerfile -t cua-image .
#  docker run --rm -it --name cua-image -p 5900:5900 -e DISPLAY=:99 cua-image
def docker_exec(cmd: str, container_name: str, decode=True) -> str | bytes:
    safe_cmd = cmd.replace('"', '\"')
    docker_cmd = f'docker exec {container_name} sh -c "{safe_cmd}"'
    output = subprocess.check_output(docker_cmd, shell=True)
    if decode:
        return output.decode("utf-8", errors="ignore")
    return output

class VM:
    def __init__(self, display, container_name):
        self.display = display
        self.container_name = container_name

vm = VM(display=":99", container_name="cua-image")

client = OpenAI()

response = client.responses.create(
    model="computer-use-preview",
    tools=[{
        "type": "computer_use_preview",
        "display_width": 1024,
        "display_height": 768,
        "environment": "browser" # other possible values: "mac", "windows", "ubuntu"
    }],
    input=[
        {
            "role": "user",
            "content": "Check the latest OpenAI news on bing.com."
        }
        # Optional: include a screenshot of the initial state of the environment
        # {
        #     type: "input_image",
        #     image_url: f"data:image/png;base64,{screenshot_base64}"
        # }
    ],
    reasoning={
        "generate_summary": "concise",
    },
    truncation="auto"
)

print(response.output)


def handle_model_action(vm, action):
    """
    Given a computer action (e.g., click, double_click, scroll, etc.),
    execute the corresponding operation on the Docker environment.
    """
    action_type = action.type

    try:
        match action_type:

            case "click":
                x, y = int(action.x), int(action.y)
                button_map = {"left": 1, "middle": 2, "right": 3}
                b = button_map.get(action.button, 1)
                print(f"Action: click at ({x}, {y}) with button '{action.button}'")
                docker_exec(f"DISPLAY={vm.display} xdotool mousemove {x} {y} click {b}", vm.container_name)

            case "scroll":
                x, y = int(action.x), int(action.y)
                scroll_x, scroll_y = int(action.scroll_x), int(action.scroll_y)
                print(f"Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
                docker_exec(f"DISPLAY={vm.display} xdotool mousemove {x} {y}", vm.container_name)

                # For vertical scrolling, use button 4 (scroll up) or button 5 (scroll down)
                if scroll_y != 0:
                    button = 4 if scroll_y < 0 else 5
                    clicks = abs(scroll_y)
                    for _ in range(clicks):
                        docker_exec(f"DISPLAY={vm.display} xdotool click {button}", vm.container_name)

            case "keypress":
                keys = action.keys
                for k in keys:
                    print(f"Action: keypress '{k}'")
                    # A simple mapping for common keys; expand as needed.
                    if k.lower() == "enter":
                        docker_exec(f"DISPLAY={vm.display} xdotool key 'Return'", vm.container_name)
                    elif k.lower() == "space":
                        docker_exec(f"DISPLAY={vm.display} xdotool key 'space'", vm.container_name)
                    else:
                        docker_exec(f"DISPLAY={vm.display} xdotool key '{k}'", vm.container_name)

            case "type":
                text = action.text
                print(f"Action: type text: {text}")
                docker_exec(f"DISPLAY={vm.display} xdotool type '{text}'", vm.container_name)

            case "wait":
                print(f"Action: wait")
                time.sleep(2)

            case "screenshot":
                # Nothing to do as screenshot is taken at each turn
                print(f"Action: screenshot")

            # Handle other actions here

            case _:
                print(f"Unrecognized action: {action}")

    except Exception as e:
        print(f"Error handling action {action}: {e}")

def get_screenshot(vm):
    """
    Takes a screenshot, returning raw bytes.
    """
    cmd = (
        f"export DISPLAY={vm.display} && "
        "import -window root png:-"
    )
    screenshot_bytes = docker_exec(cmd, vm.container_name, decode=False)
    return screenshot_bytes


import base64

def computer_use_loop(instance, response):
    """
    Run the loop that executes computer actions until no 'computer_call' is found.
    """
    while True:
        computer_calls = [item for item in response.output if item.type == "computer_call"]
        if not computer_calls:
            print("No computer call found. Output from model:")
            for item in response.output:
                print(item)
            break  # Exit when no computer calls are issued.

        # We expect at most one computer call per response.
        computer_call = computer_calls[0]
        last_call_id = computer_call.call_id
        action = computer_call.action

        # Execute the action (function defined in step 3)
        handle_model_action(instance, action)
        time.sleep(1)  # Allow time for changes to take effect.

        # Take a screenshot after the action (function defined in step 4)
        screenshot_bytes = get_screenshot(instance)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        # Send the screenshot back as a computer_call_output
        response = client.responses.create(
            model="computer-use-preview",
            previous_response_id=response.id,
            tools=[
                {
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "browser"
                }
            ],
            input=[
                {
                    "call_id": last_call_id,
                    "type": "computer_call_output",
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ],
            truncation="auto"
        )

    return response


response = computer_use_loop(vm, response)