from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.responses.create(
  model="gpt-4o",
  input=[
    {
      "role": "system",
      "content": [
        {
          "type": "input_text",
          "text": "You are Informo, a helpful AI."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "What is the weather forecast for Tuesday March 25, 2025 for Stevens Pass? Just give me High a low temperature"
        }
      ]
    }
  ],
  text={
    "format": {
      "type": "text"
    }
  },
  reasoning={},
  tools=[
    {
      "type": "web_search_preview",
      "user_location": {
        "type": "approximate"
      },
      "search_context_size": "low"
    }
  ],
  temperature=0,
  max_output_tokens=2048,
  top_p=0,
  store=False
)

print(response.output[1].content[0].annotations)
print(response.output[1].content[0].text)
print(response)
