#!/usr/bin/env python3
"""
Example of using custom XML tools with agentuse
"""

import agentuse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the agent
agentuse.configure(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    model="qwen/qwen3-32b",
    provider_order=["Cerebras"],
    instructions="Ask the human for guidance at key decision points, but not too frequently. Only ask when you genuinely need input on important choices or when stuck."
)

# Define custom tool callbacks
def ask_human_callback(content: str) -> str:
    """Ask human for input"""
    print(f"\n🤔 HUMAN INPUT NEEDED: {content}")
    response = input("Your response: ")
    return response

# Register only the ask_human tool
agentuse.add_tool("<ask_human>question for the human</ask_human>", ask_human_callback)

# Run agent with custom tools available
print("Running agent with ask_human tool...")
print("The agent can ask you questions using:")
print("- <ask_human>question for the human</ask_human>\n")

agentuse.run(
    goal="Build a complete web application with both frontend and backend. Create a task management system with user authentication, real-time updates, and data persistence. Choose appropriate technologies and architecture.",
    cli_cmd="claude",
    time_limit=15
)

# You can also remove tools if needed
# agentuse.remove_tool("<ask_human>question for the human</ask_human>")
