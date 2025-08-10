#!/usr/bin/env python3

from agentuse import AgentUse
import multiprocessing
import time
import os
from dotenv import load_dotenv

load_dotenv()

def basic_example():
    print("🤖 Running basic agent example...")
    
    agent = AgentUse(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        model="qwen/qwen3-32b",
        provider_order=["Cerebras"]
    )
    
    # Show previous sessions (optional)
    agent.show_previous_sessions()
    
    agent.run(
        goal="create a simple Python calculator that adds two numbers",
        cli_cmd="claude",
        time_limit=3,
        first_command="/init",  # Auto-send this when claude loads
        directory="/tmp/calculator_project"  # Work in specific directory
        # clone_from="~/project_templates/python_basic"  # Optional: clone template
    )

def parallel_example():
    print("🚀 Running parallel agents example...")
    
    def task1():
        agent = AgentUse(api_key=os.environ.get("OPENROUTER_API_KEY"))
        agent.run(
            goal="create a web scraper", 
            cli_cmd="claude",
            first_command="/init"
        )
    
    def task2():
        time.sleep(3)
        agent = AgentUse(api_key=os.environ.get("OPENROUTER_API_KEY"))
        agent.run(
            goal="write documentation", 
            cli_cmd="claude",
            first_command="/init"
        )
    
    p1 = multiprocessing.Process(target=task1)
    p2 = multiprocessing.Process(target=task2)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
    
    print("✅ Both agents completed!")

if __name__ == "__main__":
    print("AgentUse - Example Usage")
    print("========================")
    
    basic_example()
    # parallel_example()