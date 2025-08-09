#!/usr/bin/env python3
"""
Example usage of agent_simple library
"""

import agentuse
import multiprocessing
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure using environment variable
agentuse.configure(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    model="qwen/qwen3-32b",
    provider_order=["Cerebras"]
)

def basic_example():
    """Basic single agent example with hard timer (force quits)"""
    print("🤖 Running basic agent example...")
    
    agentuse.run(
        goal="create a simple Python calculator that adds two numbers",
        cli_cmd="claude",
        time_limit=3  # Hard timer - will force quit after 3 minutes
    )

def soft_timer_example():
    """Example with soft timer (stays at 0, doesn't quit)"""
    print("🕐 Running soft timer example...")
    
    agentuse.run(
        goal="write a web scraper for news articles",
        cli_cmd="claude", 
        time_limit=5,
        soft_timer=True  # Soft timer - timer shows "EXPIRED" but keeps running
    )

def parallel_example():
    """Multiple agents working in parallel"""
    print("🚀 Running parallel agents example...")
    
    def task1():
        agentuse.run("create a web scraper", cli_cmd="claude")
    
    def task2():
        time.sleep(3)  # Avoid window conflicts
        agentuse.run("write documentation", cli_cmd="gemini")
    
    # Run both agents in parallel
    p1 = multiprocessing.Process(target=task1)
    p2 = multiprocessing.Process(target=task2)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
    
    print("✅ Both agents completed!")

if __name__ == "__main__":
    print("Agent Simple - Example Usage")
    print("=============================")
    
    # Uncomment the example you want to run:
    
    basic_example()
    # parallel_example()
