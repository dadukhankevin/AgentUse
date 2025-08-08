# AgentUse

Like computer use, or browser use, but for agentic coding CLIs.

## Features

- 🤖 **Autonomous CLI Control**: Agents can control any CLI tool (Claude Code, Cursor CLI, Gemini CLI, Qwen, etc.)
- **Parallel Execution**: Run multiple agents simultaneously 
- **Visible Terminals**: See what your agents are doing in real Terminal windows
- **Simple API**: Just configure once and run with a single function call
- **Goal-Oriented**: Agents work toward specific objectives with time limits

## Installation

```bash
pip install openai pexpect python-dotenv
```

## Quick Start

```python
import agent_simple
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()
agent_simple.configure(api_key=os.environ.get("OPENROUTER_API_KEY"))

# Run an agent
agent_simple.run(
    goal="create a simple Python calculator",
    cli_cmd="claude",
    time_limit=5  # 5 minutes
)
```

## Configuration

### OpenRouter (Default)
```python
agent_simple.configure(
    api_key="sk-your-openrouter-key"
    # Defaults: Claude 3.5 Sonnet via OpenRouter
)

# Or specify different model/provider:
agent_simple.configure(
    api_key="sk-your-openrouter-key",
    model="anthropic/claude-4-1...",
    provider_order=["Anthropic"]
)
```

### OpenAI (Alternative)
```python
agent_simple.configure(
    api_key="sk-your-openai-key",
    model="gpt-5", 
    base_url="https://api.openai.com/v1",
    provider_order=[]
)
```

## Usage Examples

### Basic Agent
```python
import agent_simple

agent_simple.configure(api_key="your-key")

agent_simple.run(
    goal="create a web scraper for news headlines", 
    cli_cmd="claude"
)
```

### Parallel Agents
```python
import agent_simple
import multiprocessing
import time

def task1():
    agent_simple.run("create a calculator app", cli_cmd="claude")

def task2():
    time.sleep(3)  # Avoid window conflicts
    agent_simple.run("write project documentation", cli_cmd="cursor")

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=task1)
    p2 = multiprocessing.Process(target=task2)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
```

### With Time Limits
```python
agent_simple.run(
    goal="create a simple website", 
    cli_cmd="claude",
    time_limit=10  # 10 minute deadline
)
```

## Supported CLI Tools

Works with any CLI tool that accepts text input:
- `claude` - Anthropic's Claude CLI
- `cursor` - Cursor AI
- `gemini` - Google's Gemini
- `aider` - AI pair programming
- Any other CLI tool

## API Reference

### `configure(api_key, model, base_url, provider_order)`
Configure the agent with your API credentials.

**Parameters:**
- `api_key` (str): Your OpenAI or OpenRouter API key
- `model` (str): Model to use (default: "gpt-4")
- `base_url` (str): API endpoint (default: OpenAI)
- `provider_order` (list): Preferred providers for OpenRouter

### `run(goal, cli_cmd, time_limit)`
Run an agent to accomplish a specific goal.

**Parameters:**
- `goal` (str): What you want the agent to accomplish
- `cli_cmd` (str): CLI command to run (default: "claude")
- `time_limit` (int, optional): Time limit in minutes

## How It Works

1. **Terminal Creation**: Opens a new Terminal window and starts your chosen CLI tool
2. **Goal Planning**: The agent breaks down your goal into actionable steps
3. **CLI Interaction**: Sends commands and responds to prompts in the CLI
4. **Progress Tracking**: Monitors screen output and adapts strategy
5. **Completion**: Exits when the goal is achieved or time limit reached

## Requirements

- macOS (uses Terminal.app and AppleScript)
- Python 3.7+
- OpenAI API key or OpenRouter API key
- CLI tools you want to control (Claude, Cursor, etc.)

## Troubleshooting

**"API key not configured" error:**
```python
# Make sure to configure before running
agent_simple.configure(api_key="your-key")
```

**Multiple agents interfere with each other:**
```python
# Add delays between starting agents
time.sleep(3)  # Wait 3 seconds before starting next agent
```

**Terminal windows don't appear:**
- Make sure Terminal.app has accessibility permissions
- Try running with `cli_cmd="echo"` to test basic functionality

## Examples

See `example.py` for complete working examples including:
- Basic single agent usage
- Parallel multi-agent workflows  
- Different model configurations
- Error handling and best practices

## License

MIT License - see LICENSE file for details.

## Contributing

Pull requests welcome! This library aims to stay simple and focused on CLI automation.