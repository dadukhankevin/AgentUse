#!/usr/bin/env python3

import os
import tempfile
from dotenv import load_dotenv
from agentuse import AgentUse

load_dotenv()

def clone_template_example():
    """Example: Clone from a template directory"""
    print("📁 Running agent with directory cloning...")
    
    # Create a temporary template directory with some starter files
    template_dir = "/tmp/my_template"
    os.makedirs(template_dir, exist_ok=True)
    
    # Create some template files
    with open(f"{template_dir}/README.md", "w") as f:
        f.write("# Project Template\n\nStarting template for new projects.\n")
    
    with open(f"{template_dir}/package.json", "w") as f:
        f.write('{\n  "name": "starter-template",\n  "version": "1.0.0"\n}\n')
    
    os.makedirs(f"{template_dir}/src", exist_ok=True)
    with open(f"{template_dir}/src/main.py", "w") as f:
        f.write("# Main application file\nprint('Hello World!')\n")
    
    print(f"📄 Created template at: {template_dir}")
    
    # Create a new project directory
    project_dir = "/tmp/my_new_project"
    
    agent = AgentUse(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        model="qwen/qwen3-32b",
        provider_order=["Cerebras"]
    )
    
    agent.run(
        goal="Enhance this template into a full Python web application with FastAPI",
        cli_cmd="claude",
        directory=project_dir,           # Work in this directory
        clone_from=template_dir,         # 🎯 Clone template first
        first_command="/init",
        time_limit=8
    )

def clone_previous_work():
    """Example: Continue from previous agent's work"""
    print("🔄 Continuing from previous agent session...")
    
    agent = AgentUse(api_key=os.environ.get("OPENROUTER_API_KEY"))
    
    agent.run(
        goal="Add tests and documentation to the existing codebase",
        cli_cmd="claude", 
        directory="/tmp/continued_project",
        clone_from="/tmp/my_new_project",  # Continue from previous work
        first_command="/init"
    )

def clone_real_project():
    """Example: Clone from an actual existing project"""
    agent = AgentUse(api_key=os.environ.get("OPENROUTER_API_KEY"))
    
    agent.run(
        goal="Refactor this codebase to use modern Python patterns",
        cli_cmd="claude",
        directory="/tmp/refactored_version", 
        clone_from="~/existing_project",     # Clone from home directory
        first_command="/init",
        time_limit=15
    )

if __name__ == "__main__":
    print("Clone Directory Examples")
    print("========================")
    
    clone_template_example()
    # clone_previous_work()
    # clone_real_project()
