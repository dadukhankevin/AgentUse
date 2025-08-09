import os
import time
import re
import subprocess
from typing import Optional
import openai

def get_system_prompt(goal: Optional[str] = None, custom_tools=None, instructions=None):
    goal_text = f"\n\nGOAL: {goal}" if goal else ""
    base = f"""You are a PROJECT MANAGER directing a coding assistant. You make all decisions and give clear instructions.{goal_text}

YOU DECIDE EVERYTHING. The assistant implements what you tell them.

OUTPUT FORMAT: One XML command only.

Commands:
- <prompt>specific instruction</prompt>
- <wait/>
- <exit/>"""
    
    if custom_tools:
        base += "\n\nCustom Tools:"
        for tool_format in custom_tools:
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
    
    if instructions:
        base += f"\n\nADDITIONAL INSTRUCTIONS:\n{instructions}"
    
    return base

def clean_output(text: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    text = re.sub(r"\x1b\[[?][0-9;]*[lh]", "", text)
    text = re.sub(r"\x1b\[.*?[A-Za-z]", "", text)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    return text

class Driver:
    def __init__(self, cmd: str, directory: Optional[str] = None):
        cwd = directory or os.getcwd()
        
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
        
        startup_command = f"export NO_COLOR=1 && export CLICOLOR=0 && clear && {cmd}"
        self._type_and_enter(startup_command)
        time.sleep(2)

    def _type_and_enter(self, text: str):
        if text:
            self._type_text(text)
        self._press_enter()
        time.sleep(0.2)

    def _type_text(self, text: str):
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
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        return result.stdout.strip()

    def close(self):
        pass

class Agent:
    def __init__(self, goal: str, driver: Driver, time_limit_minutes: Optional[int], client, custom_tools, model, provider_order):
        self.goal = goal
        self.driver = driver
        self.client = client
        self.custom_tools = custom_tools
        self.model = model
        self.provider_order = provider_order
        self.message_history = [
            {"role": "system", "content": get_system_prompt(goal, custom_tools)},
            {"role": "user", "content": f"{goal}"}
        ]
        self.transcript = ""
        self.previous_transcript = ""
        self.start_time = time.time()
        self.time_limit_minutes = time_limit_minutes
        self.last_screen_change_time = time.time()
        self.screen_stable_threshold = 0.5

    def get_new_terminal_content(self, current_screen: str) -> str:
        if not self.previous_transcript:
            return current_screen[-30000:] if len(current_screen) > 30000 else current_screen
        
        if self.previous_transcript in current_screen:
            prev_end = current_screen.rfind(self.previous_transcript) + len(self.previous_transcript)
            new_content = current_screen[prev_end:]
            
            if len(new_content) > 30000:
                new_content = new_content[-30000:]
            
            return new_content
        else:
            return current_screen[-30000:] if len(current_screen) > 30000 else current_screen

    def summarize_terminal_output(self, new_content: str) -> str:
        if not new_content.strip():
            return "Terminal is empty/idle"
        
        extra_body = {"provider": {"order": self.provider_order}} if self.provider_order else {}
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Summarize terminal output in 1-2 concise lines. Focus on what's happening, any prompts, errors, or key information."},
                {"role": "user", "content": f"New terminal content:\n{new_content}"}
            ],
            temperature=0.3,
            extra_body=extra_body,
        )
        return resp.choices[0].message.content.strip()

    def ask_llm(self) -> str:
        time_status = self.get_time_status()
        
        messages = self.message_history.copy()
        if time_status:
            messages.append({"role": "user", "content": f"TIME STATUS: {time_status}"})
        
        extra_body = {"provider": {"order": self.provider_order}} if self.provider_order else {}
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            extra_body=extra_body,
        )
        return (resp.choices[0].message.content or "").strip()

    def get_time_status(self) -> str:
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
        
        for tool_format, callback in self.custom_tools.items():
            if ">" in tool_format and "</" in tool_format:
                start_tag = tool_format.split(">")[0] + ">"
                end_tag = "</" + tool_format.split(">")[0].split("<")[1] + ">"
                
                if cmd.startswith(start_tag) and cmd.endswith(end_tag):
                    content = cmd[len(start_tag):-len(end_tag)]
                    result = callback(content)
                    self.message_history.append({"role": "user", "content": f"Tool result: {result}"})
                    return "custom_tool"
        
        print(f"\n[INVALID XML command: {cmd}]")
        return "wait"

    def run(self):
        time.sleep(2)
        
        while True:
            current_screen = self.driver.read_screen()
            clean_screen = clean_output(current_screen)

            if clean_screen != self.transcript:
                print("\n[Screen updated]")
                
                new_content = self.get_new_terminal_content(clean_screen)
                
                self.previous_transcript = self.transcript
                self.transcript = clean_screen
                self.last_screen_change_time = time.time()
                
                if new_content.strip():
                    summary = self.summarize_terminal_output(new_content)
                    self.message_history.append({"role": "user", "content": f"Terminal: {summary}"})
                
                continue
            
            time_since_last_change = time.time() - self.last_screen_change_time
            if time_since_last_change < self.screen_stable_threshold:
                time.sleep(0.1)
                continue
            
            if self.time_limit_minutes:
                elapsed_minutes = (time.time() - self.start_time) / 60
                if elapsed_minutes >= self.time_limit_minutes:
                    print("\n[TIME LIMIT EXPIRED - Forcing exit]")
                    break
            
            directive = self.ask_llm()
            print(f"\n[Agent: {directive}]")
            
            self.message_history.append({"role": "assistant", "content": directive})
            
            result = self.act(directive)

            if result == "wait":
                time.sleep(0.5)
                continue

            if result == "exit":
                print("\n[Goal accomplished!]")
                break

            time.sleep(0.3)

class AgentUse:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet", base_url: str = "https://openrouter.ai/api/v1", provider_order: Optional[list] = None, instructions: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.provider_order = provider_order
        self.custom_tools = {}
        self.instructions = instructions

    def add_tool(self, tool_format: str, callback):
        self.custom_tools[tool_format] = callback

    def remove_tool(self, tool_format: str):
        self.custom_tools.pop(tool_format, None)

    def get_client(self):
        return openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def run(self, goal: str, cli_cmd: str = "claude", time_limit: Optional[int] = None, directory: Optional[str] = None):
        driver = Driver(cli_cmd, directory)
        client = self.get_client()
        agent = Agent(goal, driver, time_limit, client, self.custom_tools, self.model, self.provider_order)
        agent.run()
        driver.close()

