#!/usr/bin/env python3

from agentuse import AgentUse
import os
from dotenv import load_dotenv

load_dotenv()

def ask_human_callback(content: str) -> str:
    print(f"\n🤔 HUMAN INPUT NEEDED: {content}")
    response = input("Your response: ")
    return response

agent = AgentUse(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    model="qwen/qwen3-32b",
    provider_order=["Cerebras"],
    instructions="Ask the human for guidance at key decision points, but not too frequently. Only ask when you genuinely need input on important choices or when stuck."
)

agent.add_tool("<ask_human>question for the human</ask_human>", ask_human_callback)

print("Running agent with ask_human tool...")
print("The agent can ask you questions using:")
print("- <ask_human>question for the human</ask_human>\n")

agent.run(
    goal="Build a complete web application with both frontend and backend. Create a task management system with user authentication, real-time updates, and data persistence. Choose appropriate technologies and architecture.",
    cli_cmd="claude",
    time_limit=15,
    first_command="/init",
    directory="/tmp/webapp_project"
    # clone_from="~/templates/webapp_starter"  # Optional: start with template
)