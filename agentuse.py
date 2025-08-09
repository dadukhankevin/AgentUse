import os
import time
import re
import subprocess
from typing import Optional


import openai

def get_system_prompt(goal: Optional[str] = None):
    """Build system prompt including custom tools"""
    goal_text = f"\n\nGOAL: {goal}" if goal else ""
    base = f"""You are a PROJECT MANAGER directing a coding assistant. You make all decisions and give clear instructions.{goal_text}

YOU DECIDE EVERYTHING. The assistant implements what you tell them.

OUTPUT FORMAT: One XML command only.

Commands:
- <prompt>specific instruction</prompt>
- <wait/>
- <exit/>"""
    
    if cfg.custom_tools:
        base += "\n\nCustom Tools:"
        for tool_format in cfg.custom_tools:
            base += f"\n- {tool_format}"
    
    base += """\n\nYOUR ROLE:
- Give direct, specific instructions
- Make all technical decisions yourself
- Don't ask the assistant to choose - YOU choose
- Be decisive and clear about requirements
- Keep solutions simple and focused

Examples:
<prompt>create a simple calculator that adds two numbers</prompt>
<prompt>yes, save it as calculator.py</prompt>
<prompt>1</prompt>
<exit/>

NEVER output technical syntax or code in prompts. Only give natural instructions.

When you see options or questions from the assistant, make the decision and instruct them to proceed.

Exit when the core goal is achieved - don't over-engineer.
"""
    
    if cfg.instructions:
        base += f"\n\nADDITIONAL INSTRUCTIONS:\n{cfg.instructions}"
    
    return base


class Config:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3.5-sonnet"
        self.provider_order = ["Anthropic"]
        self.custom_tools = {}  # tool_format -> callback function
        self.instructions = None

cfg = Config()

def configure(api_key: str, model: str = "anthropic/claude-3.5-sonnet", base_url: str = "https://openrouter.ai/api/v1", provider_order: Optional[list] = None, instructions: Optional[str] = None):
    """Configure the agent with your API credentials and model preferences.
    
    Args:
        api_key: Your OpenRouter API key (or OpenAI API key if using OpenAI)
        model: Model to use (e.g., "anthropic/claude-3.5-sonnet", "gpt-4", "qwen/qwen3-32b")
        base_url: API base URL (default OpenRouter, use "https://api.openai.com/v1" for OpenAI)
        provider_order: List of preferred providers (for OpenRouter, e.g., ["Anthropic", "Cerebras"])
    """
    cfg.api_key = api_key
    cfg.model = model
    cfg.base_url = base_url
    cfg.provider_order = provider_order or ["Anthropic"]
    cfg.instructions = instructions

def add_tool(tool_format: str, callback):
    """Add a custom XML tool with full format shown to LLM.
    
    Args:
        tool_format: Full XML format like "<ask_human>question for human</ask_human>"
        callback: Function that receives content between tags, returns string
    """
    cfg.custom_tools[tool_format] = callback

def remove_tool(tool_format: str):
    """Remove a custom tool by its full format"""
    cfg.custom_tools.pop(tool_format, None)

def get_client():
    """Create a new OpenAI client instance for thread safety"""
    if not cfg.api_key:
        raise ValueError("API key not configured. Call agent_simple.configure(api_key='your-key') first.")
    return openai.OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

def clean_output(text: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    text = re.sub(r"\x1b\[[?][0-9;]*[lh]", "", text)
    text = re.sub(r"\x1b\[.*?[A-Za-z]", "", text)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    return text

class Driver:
    def __init__(self, cmd: str, directory: Optional[str] = None):
        # Use the approach that works properly with colors (like original agent.py)
        cwd = directory or os.getcwd()
        
        # Open a new Terminal window with just cd command
        script = f'''
        tell application "Terminal"
            activate
            do script "cd {cwd}"
            delay 0.5
            return id of front window
        end tell
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        self.window_id = result.stdout.strip()
        time.sleep(1)
        
        # Disable colors and run CLI command in one line for faster startup
        startup_command = f"export NO_COLOR=1 && export CLICOLOR=0 && clear && {cmd}"
        self._type_and_enter(startup_command)
        time.sleep(2)

    def _type_and_enter(self, text: str):
        """Type text and press Enter using System Events"""
        if text:
            self._type_text(text)
        self._press_enter()
        time.sleep(0.2)

    def _type_text(self, text: str):
        """Type text using System Events (doesn't press Enter)"""
        if text:
            esc_text = text.replace("\\", "\\\\").replace('"', '\\"')
            script = f'''
            tell application "Terminal"
                activate
                set frontmost of window id {self.window_id} to true
            end tell
            tell application "System Events"
                keystroke "{esc_text}"
            end tell
            '''
            subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
    
    def _press_enter(self):
        """Press Enter key"""
        script = f'''
        tell application "Terminal"
            activate
            set frontmost of window id {self.window_id} to true
        end tell
        tell application "System Events"
            key code 36
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)

    def send_text(self, text: str):
        # For agent prompts, type text and press Enter
        if text:
            self._type_text(text)
        self._press_enter()
        time.sleep(0.3)

    def read_screen(self) -> str:
        script = f'''
        tell application "Terminal"
            get contents of window id {self.window_id}
        end tell
        '''
        try:
            result = subprocess.run(["osascript", "-e", script], 
                                  capture_output=True, text=True, check=False)
            return result.stdout.strip()
        except Exception:
            return ""

    def close(self):
        pass  # Let user manually close Terminal windows

class Agent:
    def __init__(self, goal: str, driver: Driver, time_limit_minutes: Optional[int] = None):
        self.goal = goal
        self.driver = driver
        self.message_history = [
            {"role": "system", "content": get_system_prompt(goal)},
            {"role": "user", "content": f"{goal}"}
        ]
        self.transcript = ""
        self.previous_transcript = ""
        self.start_time = time.time()
        self.time_limit_minutes = time_limit_minutes
        self.last_screen_change_time = time.time()

    def get_new_terminal_content(self, current_screen: str) -> str:
        """Extract only the new content that was added to the terminal"""
        if not self.previous_transcript:
            # First time - return the current content (up to limit)
            return current_screen[-30000:] if len(current_screen) > 30000 else current_screen
        
        # Find where the previous content ends in the current content
        if self.previous_transcript in current_screen:
            # Get everything after the previous content
            prev_end = current_screen.rfind(self.previous_transcript) + len(self.previous_transcript)
            new_content = current_screen[prev_end:]
            
            # Apply 30k character limit to new content
            if len(new_content) > 30000:
                new_content = new_content[-30000:]
            
            return new_content
        else:
            # Previous content not found (terminal was cleared or scrolled)
            # Return recent content up to limit
            return current_screen[-30000:] if len(current_screen) > 30000 else current_screen

    def summarize_terminal_output(self, new_content: str) -> str:
        """Get LLM to summarize new terminal output into 1-2 lines"""
        if not new_content.strip():
            return "Terminal is empty/idle"
        
        client = get_client()
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": "Summarize terminal output in 1-2 concise lines. Focus on what's happening, any prompts, errors, or key information."},
                {"role": "user", "content": f"New terminal content:\n{new_content}"}
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    def ask_llm(self) -> str:
        time_status = self.get_time_status()
        
        # Add time status to the latest message if needed
        messages = self.message_history.copy()
        if time_status:
            messages.append({"role": "user", "content": f"TIME STATUS: {time_status}"})
        
        client = get_client()
        extra_body = {"provider": {"order": cfg.provider_order}} if cfg.provider_order else {}
        
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            temperature=0.7,
            extra_body=extra_body,
        )
        return (resp.choices[0].message.content or "").strip()

    def get_time_status(self) -> str:
        """Get current time status and urgency level"""
        if not self.time_limit_minutes:
            return ""
        
        elapsed_minutes = (time.time() - self.start_time) / 60
        remaining_minutes = self.time_limit_minutes - elapsed_minutes
        
        if remaining_minutes <= 0:
            return "⚠️ TIME EXPIRED! Wrap up immediately and exit."
        elif remaining_minutes <= 5:
            return f"🚨 URGENT: Only {remaining_minutes:.1f} minutes left! Prioritize essential tasks and wrap up quickly."
        elif remaining_minutes <= 15:
            return f"⏰ {remaining_minutes:.1f} minutes remaining. Focus on core requirements, avoid extras."
        else:
            return f"⏱️ {remaining_minutes:.1f} minutes remaining out of {self.time_limit_minutes} total."

    def act(self, directive: str) -> str:
        cmd = directive.strip()
        if not (cmd.startswith("<") and cmd.endswith(">") and cmd.count("<") == cmd.count(">")):
            print(f"\n[INVALID XML: {cmd[:60]}...]")
            return "wait"
        if cmd == "<wait/>":
            return "wait"
        if cmd == "<exit/>":
            return "exit"
        if cmd.startswith("<prompt>") and cmd.endswith("</prompt>"):
            text = cmd[8:-9]
            self.driver.send_text(text)
            return "prompted"
        
        # Check custom tools
        for tool_format, callback in cfg.custom_tools.items():
            # Extract tag name from format like "<ask_human>...</ask_human>"
            if ">" in tool_format and "</" in tool_format:
                start_tag = tool_format.split(">")[0] + ">"
                end_tag = "</" + tool_format.split(">")[0].split("<")[1] + ">"
                
                if cmd.startswith(start_tag) and cmd.endswith(end_tag):
                    content = cmd[len(start_tag):-len(end_tag)]
                    try:
                        result = callback(content)
                        # Add custom tool result as user message (tool output)
                        self.message_history.append({"role": "user", "content": f"Tool result: {result}"})
                        return "custom_tool"
                    except Exception as e:
                        self.message_history.append({"role": "user", "content": f"Tool error: {e}"})
                        return "wait"
        
        print(f"\n[INVALID XML command: {cmd}]")
        return "wait"

    def update_summary(self, action: str):
        """Update session summary with latest action"""
        # Initialize summary if it doesn't exist
        if not hasattr(self, 'summary'):
            self.summary = "Starting session"
            
        update_prompt = f"""Previous summary: {self.summary}

Latest action: {action}
Screen result: {self.transcript[-500:]}

Provide a concise summary (2-3 sentences) that captures:
1. Key progress toward the goal: {self.goal}
2. Current state/what's been accomplished
3. Any important context for next decisions

Keep it brief but include essential details."""

        client = get_client()
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": "Create concise summaries."},
                {"role": "user", "content": update_prompt}
            ],
            temperature=0.1,
        )
        self.summary = (resp.choices[0].message.content or "").strip()

    def run(self):
        time.sleep(2)
        
        while True:
            current_screen = self.driver.read_screen()
            clean_screen = clean_output(current_screen)

            if clean_screen != self.transcript:
                print("\n[Screen updated]")
                
                # Get only the new content that was added
                new_content = self.get_new_terminal_content(clean_screen)
                
                # Update transcript tracking
                self.previous_transcript = self.transcript
                self.transcript = clean_screen
                self.last_screen_change_time = time.time()
                
                # Only summarize if there's actually new content
                if new_content.strip():
                    summary = self.summarize_terminal_output(new_content)
                    self.message_history.append({"role": "user", "content": f"Terminal: {summary}"})
                
                time.sleep(1)
                continue
            
            # Check if time limit has expired
            if self.time_limit_minutes:
                elapsed_minutes = (time.time() - self.start_time) / 60
                if elapsed_minutes >= self.time_limit_minutes:
                    print("\n[TIME LIMIT EXPIRED - Forcing exit]")
                    break
            
            # Screen is stable, ask the LLM what to do
            directive = self.ask_llm()
            print(f"\n[Agent: {directive}]")
            
            # Store the assistant's XML response
            self.message_history.append({"role": "assistant", "content": directive})
            
            result = self.act(directive)

            if result == "wait":
                time.sleep(2)
                continue

            # Continue to next iteration

            if result == "exit":
                print("\n[Goal accomplished!]")
                break

            time.sleep(1.5)

def run(goal: str, cli_cmd: str = "claude", time_limit: Optional[int] = None, directory: Optional[str] = None):
    """Run an agent to accomplish a goal using a CLI tool.
    
    Args:
        goal: What you want the agent to accomplish
        cli_cmd: CLI command to run (e.g., "claude", "gemini", "cursor")
        time_limit: Optional time limit in minutes
        directory: Optional starting directory (defaults to current directory)
    """
    if not cfg.api_key:
        raise ValueError("API key not configured. Call agent_simple.configure(api_key='your-key') first.")
    
    driver = Driver(cli_cmd, directory)
    try:
        agent = Agent(goal, driver, time_limit)
        agent.run()
    finally:
        driver.close()