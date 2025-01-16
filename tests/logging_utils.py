# import sys
# import logging
# from datetime import datetime, UTC
# from hashlib import sha256
# from pathlib import Path
# import json
# from typing import Any

# from pydantic_ai.result import RunResult
# from agent_prompts import prompts
# from pydantic_ai import RunContext, Agent
# from agent_prompts import prompts
# import asyncio
# from dotenv import load_dotenv
# from display_utils import CustomPrint
# from rich.console import Console
# from rich.panel import Panel
# from rich.markdown import Markdown

# console = Console()

# load_dotenv(override=True)

# SYSTEM_PROMPT = prompts["SYSTEM_PROMPT"]
# from azure_agent import openai_model

# logging.getLogger("httpx").setLevel(logging.WARNING)

# from main_utils import ToolOutput

# run_context = RunContext(
#     deps=ToolOutput,
#     model=openai_model,
#     retry=3,
#     messages=[],
#     tool_name=None,
# )

# agent = Agent(
#     model=openai_model,
#     name="DebugAgent",
#     system_prompt=SYSTEM_PROMPT,
#     tools=[],
# )

# class EnterpriseLogger:
#     """
#     Hybrid logger class. 
#     - You can call standard Python logging methods (log_message, log_error, etc.) from any script.
#     - The agent can also fetch logs, then summarize them before storing to JSON, or just store them raw.
#     """

#     def __init__(self, user_email: str):
#         self.session_id = sha256(user_email.encode()).hexdigest()
#         self.customPrint = CustomPrint()
#         self.agent: Agent[None, str] = agent
#         self.context: RunContext[type[ToolOutput]] = run_context

#         log_dir = Path("logs")
#         log_dir.mkdir(exist_ok=True)
#         log_file = log_dir / f"azure_agent_{self.session_id}.log"

#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#             handlers=[
#                 logging.FileHandler(filename=log_file, mode="a"),
#                 logging.StreamHandler(stream=sys.stdout)
#             ]
#         )
#         self.logit = logging.getLogger(agent.name)

#     def log_message(self, message: str, level: str = "info", log: bool = True, print_msg: bool = True) -> None:
#         """
#         Writes a message to the .log file and optionally prints to console.
#         """
#         timestamp = datetime.now(UTC).isoformat()
#         log_entry = f"[{timestamp}] [{self.session_id}] {message}"

#         if log:
#             if level == "error":
#                 self.logit.error(log_entry)
#             elif level == "warning":
#                 self.logit.warning(log_entry)
#             elif level == "success":
#                 self.logit.info(log_entry)
#             else:
#                 self.logit.info(log_entry)

#         if print_msg:
#             style_map = {
#                 "error": "red",
#                 "warning": "yellow",
#                 "success": "green",
#                 "info": "blue"
#             }
            
#             # If the message appears to be a table (has borders), print directly
#             if "╭" in message or "├" in message:
#                 console.print(message)
#             else:
#                 # Otherwise treat as markdown
#                 md = Markdown(message, style="default")
#                 console.print(Panel(
#                     md,
#                     title=level.title(),
#                     border_style=style_map[level]
#                 ))

#     def format_error(self, error: Exception, context: Any = None) -> str:
#         error_text = f"""
# ## Error Details
# **Type:** {type(error).__name__}
# **Error:** {str(error)}"""
#         if context:
#             error_text += f"\n**Context:** {context}"
#         return error_text

#     def log_error(self, error: Exception, log: bool = True, print_msg: bool = True) -> None:
#         """
#         Writes an error entry to the .log file and optionally prints it.
#         """
#         error_message = self.format_error(error)
#         self.log_message(error_message, level="error", log=log, print_msg=print_msg)
#         if log:
#             self.logit.error("Full traceback:", exc_info=error)

#     def log_success(self, message: str, log: bool = True, print_msg: bool = True) -> None:
#         """
#         Writes a success (info) entry to the .log file and optionally prints it.
#         """
#         self.log_message(message, level="success", log=log, print_msg=print_msg)

#     def _raw_log_file_path(self) -> Path:
#         """Returns the path to the raw .log file for this session."""
#         return Path("logs") / f"azure_agent_{self.session_id}.log"

#     @agent.tool_plain
#     def fetch_raw_logs(self, lines: int = 500) -> ToolOutput:
#         """
#         Returns the last 'lines' lines of the raw .log file for this session, or all lines if fewer than 'lines' exist.
#         """
#         log_file = self._raw_log_file_path()
#         if not log_file.exists():
#             return ToolOutput(success=False, error="No raw log file found for this session.")
#         try:
#             with open(log_file, "r", encoding="utf-8") as f:
#                 all_lines = f.readlines()
#             snippet = "".join(all_lines[-lines:])  # last X lines
#             return ToolOutput(success=True, result=snippet)
#         except Exception as e:
#             return ToolOutput(success=False, error=str(e))

#     @agent.tool_plain
#     async def summarize_and_save_logs(self, lines: int = 500) -> ToolOutput:
#         """
#         1) Fetches the last n 'lines' lines from the raw .log file.
#         2) Asks the LLM to summarize them.
#         3) Saves the summary to azure_log_<session_id>.json
#         """
#         raw_logs_res = self.fetch_raw_logs(lines)
#         if not raw_logs_res.success:
#             return raw_logs_res  # pass forward any error

#         prompt_text = (
#             "Please summarize the following log snippet. Highlight key events, errors, and any other crucial info:\n\n"
#             f"{raw_logs_res.result}"
#         )

#         try:
#             # Use the agent to get a summary
#             summary_res: RunResult[str] = await self.agent.run(user_prompt=prompt_text)
#             if not summary_res or not summary_res.data:
#                 return ToolOutput(success=False, error="LLM was unable to provide a summary.")

#             summary_text = summary_res.data

#             # Save to JSON
#             store_res = self.store_log_json(summary_text, is_summary=True)
#             if not store_res.success:
#                 return store_res

#             return ToolOutput(
#                 success=True,
#                 result=f"Summary saved to JSON: {store_res.result}",
#                 output=summary_text
#             )
#         except Exception as e:
#             return ToolOutput(success=False, error=str(e))

#     @agent.tool_plain
#     def store_log_json(self, content: str, is_summary: bool = False) -> ToolOutput:
#         """
#         Persists either the raw logs or LLM summary into azure_log_<session_id>.json
#         The agent decides whether to store the raw logs or a summary via is_summary param.
#         """
#         try:
#             log_dir = Path("logs")
#             log_dir.mkdir(exist_ok=True)

#             # If the file already exists, load old content to keep a history
#             log_file = log_dir / f"azure_log_{self.session_id}.json"
#             existing_data = {}
#             if log_file.exists():
#                 with open(log_file, "r", encoding="utf-8") as f:
#                     existing_data = json.load(f)

#             new_entry = {
#                 "timestamp": datetime.now(UTC).isoformat(),
#                 "session_id": self.session_id,
#                 "is_summary": is_summary,
#                 "content": content
#             }

#             # Merge the new entry with existing data
#             if "history" not in existing_data:
#                 existing_data["history"] = []
#             existing_data["history"].append(new_entry)

#             with open(log_file, "w", encoding="utf-8") as f:
#                 json.dump(existing_data, f, indent=2)

#             return ToolOutput(success=True, result=str(log_file))
#         except Exception as e:
#             return ToolOutput(success=False, error=str(e))

#     @agent.tool_plain
#     def get_log_content(self) -> ToolOutput:
#         """
#         Loads all stored JSON logs (both raw and summarized entries).
#         """
#         try:
#             log_file = Path("logs") / f"azure_log_{self.session_id}.json"
#             if not log_file.exists():
#                 return ToolOutput(success=False, error=f"Log file not found for session: {self.session_id}")

#             with open(log_file, "r", encoding="utf-8") as f:
#                 log_data = json.load(f)
#             return ToolOutput(success=True, result=log_data)
#         except Exception as e:
#             return ToolOutput(success=False, error=str(e))

#     @agent.tool_plain
#     @staticmethod
#     def list_log_sessions() -> ToolOutput:
#         """
#         Returns a list of available session JSON logs in 'logs/' directory.
#         """
#         try:
#             log_dir = Path("logs")
#             if not log_dir.exists():
#                 return ToolOutput(success=True, result=[])

#             log_files = list(log_dir.glob("azure_log_*.json"))
#             sessions = []

#             for log_file in log_files:
#                 try:
#                     with open(log_file, "r", encoding="utf-8") as f:
#                         log_data = json.load(f)
#                         # If there's at least one entry in 'history', grab the first
#                         if "history" in log_data and len(log_data["history"]) > 0:
#                             first_entry = log_data["history"][0]
#                             sessions.append({
#                                 "session_id": first_entry["session_id"],
#                                 "timestamp": first_entry["timestamp"]
#                             })
#                 except Exception:
#                     continue

#             return ToolOutput(success=True, result=sessions)
#         except Exception as e:
#             return ToolOutput(success=False, error=str(e))

#     @agent.tool_plain
#     @staticmethod
#     def cleanup_old_logs(max_age_days: int = 7) -> ToolOutput:
#         """
#         Removes JSON logs older than 'max_age_days' from 'logs/' directory.
#         """
#         try:
#             log_dir = Path("logs")
#             if not log_dir.exists():
#                 return ToolOutput(success=True, result="No logs to clean")

#             now = datetime.now(UTC)
#             removed = []

#             for log_file in log_dir.glob("azure_log_*.json"):
#                 try:
#                     with open(log_file, "r", encoding="utf-8") as f:
#                         log_data = json.load(f)
#                         # The earliest timestamp in 'history' can define the log's age
#                         if "history" not in log_data or len(log_data["history"]) == 0:
#                             log_file.unlink()
#                             removed.append(str(log_file))
#                             continue

#                         # Sort entries by date, get the oldest or newest, etc.
#                         oldest_timestamp = None
#                         for entry in log_data["history"]:
#                             entry_time = datetime.fromisoformat(entry["timestamp"])
#                             if not oldest_timestamp or entry_time < oldest_timestamp:
#                                 oldest_timestamp = entry_time

#                         if oldest_timestamp and (now - oldest_timestamp).days > max_age_days:
#                             log_file.unlink()
#                             removed.append(str(log_file))
#                 except Exception:
#                     continue

#             return ToolOutput(success=True, result=f"Removed {len(removed)} old log files")
#         except Exception as e:
#             return ToolOutput(success=False, error=str(e))


# if __name__ == "__main__":
#     # Standard usage from a script perspective
#     test_logit = EnterpriseLogger("djtelicloud@gmail.com")

#     test_logit.log_message("Testing an info-level message.")
#     test_logit.log_error(Exception("Simulated error to test logging."))
#     test_logit.log_success("Operation completed successfully (test).")
    
#     # Test markdown rendering
#     test_md = """
# # Markdown Test

# This is a **bold** test with some *italics* and a [link](https://www.anthropic.com).

# - List item 1
# - List item 2
# """
#     test_logit.log_message(test_md)
