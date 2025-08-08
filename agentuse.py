import os
import time
import re
import subprocess
from typing import Optional

import pexpect  # type: ignore
import openai

SYSTEM_PROMPT = """You are a PROJECT MANAGER directing a coding assistant. You make all decisions and give clear instructions.

YOU DECIDE EVERYTHING. The assistant implements what you tell them.

OUTPUT FORMAT: One XML command only.

Commands:
- <prompt>specific instruction</prompt>
- <wait/>
- <exit/>

YOUR ROLE:
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

class Config:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3.5-sonnet"
        self.provider_order = ["Anthropic"]

cfg = Config()

def configure(api_key: str, model: str = "anthropic/claude-3.5-sonnet", base_url: str = "https://openrouter.ai/api/v1", provider_order: list = ["Anthropic"]):
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
    cfg.provider_order = provider_order

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
    def __init__(self, cmd: str):
        # Use the approach that works properly with colors (like original agent.py)
        cwd = os.getcwd()
        
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
        self.summary = "Session just started."
        self.transcript = ""
        self.start_time = time.time()
        self.time_limit_minutes = time_limit_minutes
        self.last_screen_change_time = time.time()

    def ask_llm(self) -> str:
        time_status = self.get_time_status()
        time_prompt = f"\n\nTIME STATUS: {time_status}" if time_status else ""
        
        prompt = f"""Goal: {self.goal}

Session Summary: {self.summary}{time_prompt}

Current screen:
{self.transcript[-1000:]}

What should I do next?"""
        
        client = get_client()
        extra_body = {"provider": {"order": cfg.provider_order}} if cfg.provider_order else {}
        
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
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
        print(f"\n[INVALID XML command: {cmd}]")
        return "wait"

    def update_summary(self, action: str):
        """Update session summary with latest action"""
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
                self.transcript = clean_screen
                self.last_screen_change_time = time.time()
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
            result = self.act(directive)

            if result == "wait":
                time.sleep(2)
                continue

            # Update session summary with this action
            self.update_summary(directive)

            if result == "exit":
                print("\n[Goal accomplished!]")
                break

            time.sleep(1.5)

def run(goal: str, cli_cmd: str = "claude", time_limit: Optional[int] = None):
    """Run an agent to accomplish a goal using a CLI tool.
    
    Args:
        goal: What you want the agent to accomplish
        cli_cmd: CLI command to run (e.g., "claude", "gemini", "cursor")
        time_limit: Optional time limit in minutes
    """
    if not cfg.api_key:
        raise ValueError("API key not configured. Call agent_simple.configure(api_key='your-key') first.")
    
    driver = Driver(cli_cmd)
    try:
        agent = Agent(goal, driver, time_limit)
        agent.run()
    finally:
        driver.close()