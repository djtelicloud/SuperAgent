#Python 3.10.0
#Pydantic-AI 0.0.1.115

import asyncio
import re
from rich.table import Table
from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel
from logging_utils import EnterpriseLogger
from pydantic_ai import Agent
from pydantic_ai.result import RunResult
from pydantic_ai.exceptions import UnexpectedModelBehavior

from agent_prompts import prompts
from pydantic import BaseModel, Field
from azure_agent import openai_model
from messages_util import process_agent_messages, create_tool_result_table

user_email="djtelicloud@gmail.com"
logit = EnterpriseLogger(user_email=user_email)
console = Console(record=True)

SYSTEM_PROMPT = """
You are self thinking agent. you are given a task and you need to think and plan the task and execute the task.
Create step by step plan to execute the task.
Create step by step execution plan of user task and tools needed to execute the task.
Then execute the task and return the execution result. Success or Failure.
If the task is not successful, then return the next action to be taken.
Once the task is given and user is not satisfied with the result, then user can ask for modification of the task.
Use your message history to understand the user's requirements and the task.
If there is no next action, and what the user asked is completed, then return the task status as Completed.

Available tools:
- run_command: Execute terminal commands safely
- message_user: Display formatted messages to the user
- think_and_plan: Log internal thoughts and planning
"""

class ActionResult(BaseModel):
    env_check: str = Field(description="Environment check of the system you are in")
    think_and_plan: str = Field(description="Step by step thinking and planning of user task")
    execution_plan: str = Field(description="Detailed execution plan of user task and tools needed to execute the task")
    execution_result: str = Field(description="Result of the execution of the user task and status of the execution")
    next_action: str = Field(description="Next action to be taken")
    task_status: str = Field(description="Completed or Inprogress or Failed or UserFeedback")

import platform
import subprocess

superAgent = Agent(
    model=openai_model,
    name="SuperAgent",
    system_prompt=SYSTEM_PROMPT,
    result_type=ActionResult,
    tools=[
        
    ]
)

@superAgent.tool_plain
def run_command(command, shell_preference=None):
    """Execute terminal commands safely with shell control and parse complex outputs.
    shell_preference is the shell to be used. It can be powershell, cmd or default.
    If shell_preference is not provided, then default to powershell.
    If the command fails, then return the environment information and the error message.
    If the command is successful, then return the output of the command.
    Assume that the command is executed in the current directory.
    Assume Windows is the operating system on first run, unless the user specifies otherwise or the command fails.
    Assume that the user is using the default shell on Windows.
    If the command fails, then return the environment information and the error message.
    If the command is successful, then return the output of the command.
    """
    system_name: str = platform.system().lower()
    result = {
        "stdout": "",
        "stderr": "",
        "returncode": None,
        "env_check": None
    }

    try:
        if system_name == 'windows':
            if shell_preference is None:
                shell_preference = 'powershell'

            if shell_preference.lower() == 'powershell':
                process = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True
                )
            elif shell_preference.lower() == 'cmd':
                process = subprocess.run(
                    ["cmd", "/c", command],
                    capture_output=True,
                    text=True
                )
            else:
                process = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True
                )
        else:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)

        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["returncode"] = process.returncode

        if process.returncode != 0:
            result["env_check"] = platform.platform()

    except Exception as e:
        result["stderr"] = str(e)
        result["env_check"] = platform.platform()

    return result


def format_as_markdown(data):
    """Convert various data types to markdown-friendly format with proper type checking."""
    # Handle None type
    if data is None:
        return "N/A"
    
    # Handle RunResult type specifically
    if hasattr(data, '_all_messages'):
        return format_as_markdown(data.data)
    
    # Handle Pydantic models
    if hasattr(data, 'dict'):
        try:
            return format_as_markdown(data.dict())
        except (AttributeError, TypeError):
            # If dict() fails, try __dict__ or model_dump()
            try:
                return format_as_markdown(data.model_dump())
            except AttributeError:
                return format_as_markdown(data.__dict__)
    
    # Handle dictionary type
    if isinstance(data, dict):
        formatted_items = []
        for key, value in data.items():
            if key.startswith('_'):  # Skip private attributes
                continue
            formatted_value = format_as_markdown(value)
            if formatted_value and formatted_value.strip():  # Only add non-empty values
                # Special handling for stdout/stderr
                if key in ['stdout', 'stderr'] and formatted_value:
                    formatted_items.append(f"**{key}**:\n```\n{formatted_value}\n```")
                else:
                    formatted_items.append(f"**{key}**: {formatted_value}")
        return "\n".join(formatted_items)
    
    
    # Handle list/tuple types
    if isinstance(data, (list, tuple)):
        return "\n".join(f"- {format_as_markdown(item)}" for item in data if str(item).strip())
    
    # Handle string type with special formatting
    if isinstance(data, str):
        # Clean up the string and handle newlines
        cleaned = data.strip()
        if not cleaned:
            return ""
        # Handle markdown code blocks
        if "```" in cleaned:
            return cleaned
        # Handle normal text with proper line breaks
        return cleaned.replace("\n", "\n\n")
    
    # Handle numeric types
    if isinstance(data, (int, float)):
        return str(data)
    
    # Handle boolean type
    if isinstance(data, bool):
        return "✓" if data else "✗"
    
    # Default case: convert to string and clean up
    return str(data).strip()

def display_aggregated_results(response: ActionResult):
    """Display aggregated results in a concise, well-formatted table."""
    console = Console()
    
    # Create main summary table
    summary_table = Table(
        title="Task Summary",
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )
    
    # Add columns
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    # Add rows with cleaned and formatted data
    if hasattr(response, 'execution_result'):
        result = format_as_markdown(response.execution_result)
        summary_table.add_row("Result", result)
    
    if hasattr(response, 'task_status'):
        status_icon = "✓" if response.task_status in ["Completed", "UserFeedback"] else "⚠"
        summary_table.add_row("Status", f"{status_icon} {response.task_status}")
    
    # Display the table
    console.print(summary_table)
    
    # If there are next steps, display them in a separate panel without recursion
    if hasattr(response, 'next_action') and response.next_action:
        next_steps = Panel(
            Markdown(format_as_markdown(response.next_action)),
            title="Next Steps",
            border_style="blue"
        )
        console.print(next_steps)  # Just print the panel, don't call recursively

@superAgent.tool_plain
def message_user(response: ActionResult, action_name: str):
    """Display a message to the user with proper formatting."""
    display_aggregated_results(response)

@superAgent.tool_plain
async def think_and_plan(thought: str):
    """Log internal thoughts and plans without calling other tools."""
    logit.log_message(f"## Thinking\n{thought}", level="info")

@superAgent.tool_plain
async def process_tasks(message, message_history):
    """
    Process user tasks and handle different types of responses from the agent.
    Handles tool calls, tool returns, data responses, and validation errors.
    """
    try:
        logit.log_message(f"## User Input\n{message}", level="info")

        if message_history:
            response: RunResult[ActionResult] = await superAgent.run(
                user_prompt=message,
                message_history=message_history
            )
        else:
            response: RunResult[ActionResult] = await superAgent.run(
                user_prompt=message,
            )
        
        # Log the response for debugging
        if response.data:
            response_data = response.data.model_dump_json()
            logit.log_message(f"## Agent:\n{response_data}", level="success")
        # Process messages and track tool results using the utility function
        tool_results = process_agent_messages(response)

        # Check task status and return appropriate response
        if response.data.task_status in ["Completed", "Failed", "UserFeedback"]:
            # Display final results table if there were any tool calls
            if tool_results:
                summary_table = Table(
                    title="Tool Usage Summary",
                    show_header=True,
                    header_style="bold magenta",
                    border_style="blue"
                )
                summary_table.add_column("Tool", style="cyan")
                summary_table.add_column("Calls", style="green", justify="right")
                
                for tool, calls in tool_results.items():
                    summary_table.add_row(tool, str(calls))
                
                console.print(summary_table)
                logit.log_message(f"## Tool Usage Summary\n{summary_table}", level="info")
                 # Display the final results using our enhanced display function
                if response.data:
                    display_aggregated_results(response.data)
                else:
                    display_aggregated_results(response.data)
                return response
        
        

    except UnexpectedModelBehavior as e:
        error_panel = Panel(
            Markdown(f"**Model Error**: {str(e)}"),
            title="Model Error",
            border_style="red"
        )
        console.print(error_panel)
        return str(e)
        
    except Exception as e:
        error_panel = Panel(
            Markdown(f"**Error**: {str(e)}"),
            title="Unexpected Error",
            border_style="red"
        )
        console.print(error_panel)
        return str(e)

async def cli_mode():
    """CLI interface for interacting with the agent."""
    welcome_text = """
# CLI Mode Initialized

Type 'exit' or 'quit' to stop.

## Available Commands
- Any text: Process as a task
- exit/quit: Exit the program
"""
    logit.log_message(welcome_text, level="success")
    
    message_history = []

    while True:
        try:
            user_input = input("> ").strip()

            if user_input.lower() in ["exit", "quit"]:
                logit.log_message("## Exiting CLI mode", level="success")
                break

            result = await process_tasks(message=user_input, message_history=message_history)
            
            # Parse tool calls from the response and update message_history
            if isinstance(result, RunResult):
                tool_results = process_agent_messages(result)
                if tool_results:
                    message_history.append(result.data)
                    display_aggregated_results(response=result.data)
                elif isinstance(result, str):
                    message_history.append(result)

            elif isinstance(result, str) and "Exception" in result:
                # Format error message nicely
                error_panel = Panel(
                    Markdown(f"**Error**: {result}"),
                    title="Error",
                    border_style="red"
                )
                console.print(error_panel)
            
        except KeyboardInterrupt:
            logit.log_message("## KeyboardInterrupt - Exiting", level="warning")
            break
            
        except Exception as e:
            error_panel = Panel(
                Markdown(f"**Error**: {str(e)}"),
                title="Unexpected Error",
                border_style="red"
            )
            console.print(error_panel)
            break

@superAgent.tool_plain
def enhanced_parse_and_display_tool_call_results(tool_name, input_data, output_data, success):
    """Enhanced display of tool call results with proper formatting."""
    console = Console()
    
    # Create main results table
    table = Table(
        title=f"Tool Call: {tool_name}",
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )
    
    # Add columns
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="green")
    
    # Format and add input data
    if input_data:
        formatted_input = format_as_markdown(input_data)
        if formatted_input.strip():
            table.add_row("Input", formatted_input)
    
    # Format and add output data
    if output_data:
        formatted_output = format_as_markdown(output_data)
        if formatted_output.strip():
            table.add_row("Output", formatted_output)
    
    # Add status with icon
    status_icon = "✓" if success else "✗"
    status_style = "green" if success else "red"
    table.add_row("Status", f"[{status_style}]{status_icon} {'Success' if success else 'Failed'}[/{status_style}]")
    
    # Display the table
    console.print(table)

@superAgent.tool_plain
def analyze_output_with_agent(output_data):
    # Simulate a deep analysis (replace with actual agent logic)
    if isinstance(output_data, dict):
        # Example: Identify key metrics or anomalies
        metrics = {key: len(value) for key, value in output_data.items() if isinstance(value, str)}
        return f"Key Metrics: {metrics}"
    return "No significant insights found."

# Example usage

enhanced_parse_and_display_tool_call_results(
    tool_name="run_command",
    input_data={"command": "ls -la"},
    output_data={"stdout": "total 0\n-rw-r--r--  1 user  staff  0 Oct  1 00:00 file.txt", "stderr": "", "returncode": 0},
    success=True
)

if __name__ == "__main__":
    asyncio.run(cli_mode())