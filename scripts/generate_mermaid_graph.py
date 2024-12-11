import os
from pathlib import Path

from dotenv import load_dotenv

from breba_docs.agent.graph_agent import GraphAgent
from breba_docs.services.document import Document

load_dotenv()

agent = GraphAgent(Document("Hello", Path()))
image = agent.graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(image)