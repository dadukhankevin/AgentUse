#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from agentuse import AgentUse

load_dotenv()

def claude_with_init():
    """Example: Agent that automatically runs /init when Claude loads"""
    print("🤖 Running agent with automatic /init command...")
    
    agent = AgentUse(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        model="qwen/qwen3-32b", 
        provider_order=["Cerebras"]
    )
    
    # Show any previous sessions first
    agent.show_previous_sessions()
    
    agent.run(
        goal="Build a simple todo app with React",
        cli_cmd="claude",
        first_command="/init",  # Automatically sent when Claude is ready
        time_limit=10
    )

def gemini_with_setup():
    """Example: Different CLI with different first command"""
    agent = AgentUse(api_key=os.environ.get("OPENROUTER_API_KEY"))
    
    agent.run(
        goal="Write a Python script to process CSV files",
        cli_cmd="gemini",
        first_command="help",  # Show gemini help first
        time_limit=5
    )

if __name__ == "__main__":
    print("First Command & Resume Examples")
    print("===============================")
    
    claude_with_init()
    # gemini_with_setup()
