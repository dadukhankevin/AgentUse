# AgentUse

Autonomous CLI control for agentic coding tools. Like computer use, but for CLI interfaces.

## Installation

```bash
git clone https://github.com/dadukhankevin/AgentUse
cd AgentUse
pip install -r requirements.txt
```

## Quick Start

```python
import agentuse

# Configure once
agentuse.configure(api_key="your-openrouter-key")

# Run agent
agentuse.run(
    goal="create a simple Python calculator",
    cli_cmd="claude",
    time_limit=5,  # minutes
    directory="/path/to/project"  # optional
)
```

## Configuration

```python
# OpenRouter (default)
agentuse.configure(api_key="sk-your-openrouter-key")

# OpenAI
agentuse.configure(
    api_key="sk-your-openai-key",
    model="gpt-5",
    base_url="https://api.openai.com/v1"
)

# Custom instructions
agentuse.configure(
    api_key="your-key",
    instructions="Always write tests first"
)
```

## Custom Tools

```python
def ask_human(question):
    return input(f"Human: {question}\nYou: ")

agentuse.add_tool("<ask_human>question</ask_human>", ask_human)
```

## API

### `run(goal, cli_cmd, time_limit, directory)`
- **goal**: What to accomplish
- **cli_cmd**: CLI tool to use (`"claude"`, `"cursor"`, etc.)
- **time_limit**: Optional minutes limit
- **directory**: Optional starting directory

### `configure(api_key, model, base_url, provider_order, instructions)`
- **api_key**: OpenRouter or OpenAI key
- **model**: Model name (default: `"anthropic/claude-3.5-sonnet"`)
- **base_url**: API endpoint
- **instructions**: Additional agent instructions

### `add_tool(format, callback)` / `remove_tool(format)`
Add custom XML tools the agent can use.

## How It Works

1. Opens Terminal window in specified directory
2. Starts your CLI tool
3. Agent manages conversation to achieve goal
4. Monitors terminal output (up to 30k chars of new content)
5. Uses custom tools if available

## Requirements

- macOS with Terminal.app
- Python 3.7+
- API key (OpenRouter recommended)
- CLI tools you want to control

## Examples

See `example.py` and `example_custom_tools.py` for complete examples.