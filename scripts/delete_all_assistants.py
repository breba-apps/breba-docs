from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai = OpenAI()

# Fetch and delete assistants
while True:
    assistants = openai.beta.assistants.list()
    if not assistants.data:
        print("No more assistants to delete.")
        break

    for assistant in assistants.data:
        try:
            openai.beta.assistants.delete(assistant.id)
            print(f"Deleted assistant: {assistant.id}")
        except Exception as e:
            print(f"Failed to delete assistant {assistant.id}: {e}")

    if assistants.data:
        last_assistant_id = assistants.data[-1].id
        assistants = openai.beta.assistants.list(after=last_assistant_id)
