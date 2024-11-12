from dotenv import load_dotenv
from openai import OpenAI


# can run with `poetry run python delete_all_assistants.py`
load_dotenv()
openai = OpenAI()
assistants = openai.beta.assistants.list()
for assistant in assistants.data:
    openai.beta.assistants.delete(assistant.id)