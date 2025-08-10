# AgentUse

Autonomous CLI control for agentic coding tools. Control any CLI interface with natural language goals.

Perfect for orchestrating Claude Code, Cursor, Gemini, and other AI development tools.

## Features

- **Natural Language Goals** - Tell it what to build, not how
- **Auto-Init Commands** - Automatically run `/init` or setup commands  
- **Directory Cloning** - Start from templates or continue previous work
- **Smart Timers** - Hard limits for time management
- **Custom Tools** - Add human interaction or external APIs
- **Session Resume** - Track progress across multiple runs
- **Hybrid Context** - Smart summarization to stay within token limits

## Quick Start

```bash
git clone https://github.com/dadukhankevin/AgentUse
cd AgentUse
pip install -r requirements.txt
```

```python
from agentuse import AgentUse
import os
from dotenv import load_dotenv

load_dotenv()

agent = AgentUse(api_key=os.environ.get("OPENROUTER_API_KEY"))

agent.run(
    goal="Build a React todo app with local storage",
    cli_cmd="claude",
    first_command="/init",              # Auto-run when ready
    directory="/tmp/todo_project",      # Work directory  
    clone_from="~/templates/react",     # Start from template
    time_limit=10                       # Minutes limit
)
```

## API

### Configuration
```python
agent = AgentUse(
    api_key="your-openrouter-key",           # Required
    model="qwen/qwen3-32b",                  # LLM model
    provider_order=["Cerebras"],             # Provider preference
    base_url="https://openrouter.ai/api/v1", # API endpoint
    instructions="Write tests for everything" # Custom instructions
)
```

### Run Parameters
```python
agent.run(
    goal="What you want to accomplish",      # Required
    cli_cmd="claude",                        # CLI to control
    first_command="/init",                   # Auto-sent command
    directory="/path/to/work",               # Working directory
    clone_from="/path/to/template",          # Clone source
    time_limit=15                            # Minutes (optional)
)
```

## Advanced Features

### Custom Tools
```python
def ask_human_callback(question: str) -> str:
    print(f"Agent asks: {question}")
    return input("Your response: ")

agent.add_tool("<ask_human>question for human</ask_human>", ask_human_callback)

agent.run(
    goal="Build a complex app - ask me about architecture decisions",
    cli_cmd="claude",
    instructions="Ask human for guidance at key decision points"
)
```

### Session Management
```python
# Show previous sessions
agent.show_previous_sessions()

# Each session auto-saves to agentuse.md
```

### Template Workflows
```python
# Stage 1: Create base
agent.run(goal="Set up foundation", directory="/tmp/stage1")

# Stage 2: Add features  
agent.run(goal="Add API", directory="/tmp/stage2", clone_from="/tmp/stage1")

# Stage 3: Deploy
agent.run(goal="Deploy", directory="/tmp/prod", clone_from="/tmp/stage2")
```

## Use Cases

**Development Workflows**
- Rapid prototyping with templates
- Code reviews and refactoring
- Adding tests to existing codebases

**Multi-Agent Orchestration**
- Parallel development on different features
- Sequential enhancement building on previous work
- Specialized roles (frontend → backend → devops)

**Learning & Exploration**
- Technology comparison with same goals
- Best practices while building
- Code analysis and explanations

## Supported CLI Tools

- **Claude Code** (`claude`) - Anthropic's development assistant
- **Cursor** (`cursor`) - AI-powered code editor
- **Gemini** (`gemini`) - Google's coding assistant  
- **Custom CLIs** - Any interactive command-line tool

## Requirements

- macOS with Terminal.app
- Python 3.7+
- API key (OpenRouter recommended)
- CLI tools you want to control

## Examples

See included example files:
- `example.py` - Basic usage
- `example_custom_tools.py` - Human interaction
- `example_clone.py` - Directory cloning
- `example_first_command.py` - Auto-init commands

## License

MIT License