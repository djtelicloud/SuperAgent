#Python 3.10.0
#Pydantic-AI 0.0.1.115

import asyncio
import re
from rich.table import Table
from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel
from pydantic_ai import Agent
from pydantic_ai.result import RunResult

from agent_prompts import prompts
from pydantic import BaseModel, Field

import platform
import subprocess
import requests
from functools import wraps
from functools import cache


user_email="djtelicloud@gmail.com"
# logit = EnterpriseLogger(user_email=user_email)
console = Console(record=True)
#Read requirements.txt and summarize the packages
@cache
def read_requirements():
    with open('requirements.txt', 'r') as file:
        requirements = file.read()
    return requirements
    

SYSTEM_PROMPT = f"""
Packages: {read_requirements()}

You are self thinking agent. you are given a task and you need to think and plan the task and execute the task.
Create step by step plan to execute the task.
Create step by step execution plan of user task and tools needed to execute the task.
Then execute the task and return the execution result. Success or Failure.
If the task is not successful, then return the next action to be taken.
Once the task is given and user is not satisfied with the result, then user can ask for modification of the task.
Use your message history to understand the user's requirements and the task.
If there is no next action, and what the user asked is completed, then return the task status as Completed.

Available tools:
- think_and_plan: Log internal thoughts and plans without calling other tools. LLM internal thoughts are not seen by user.
- explain_action_plan: #Thinking Plan, #Executing Plan, #Execution Result, #Next Action and #Task Status
- process_tasks: Takes a user prompt, passes it to the agent, handles any tool calls, and returns the final response.
- run_command: Execute terminal commands safely like python --version and shell_preference: cmd

Tool Execution Steps:
    Step 1: think_and_plan #Mandatory
    Step 2: message_user #Mandatory
    Step 3: explain_action_plan #Mandatory
    Step 4: run_command #Optional
    Step 5: think_and_plan #Mandatory
    Step 6: explain_action_plan #Mandatory
    Step 7: message_user #Mandatory
    Step 8: repeat all steps of Goal Status AFTER each  task is Completed
"""

message_history = []


class ActionResult(BaseModel):
    """
    ActionResult is a Pydantic model that represents the result of an action.
    Args:
        user_goal: Users overall goal. Don't mark status Completed until completed.
        think_and_plan: Step by step thinking and planning of user task
        execution_plan: Detailed execution plan of user task and tools needed to execute the task
        execution_result: Result of the execution of the user task and status of the execution
        goal_status: Completed or Inprogress or Failed or UserFeedback or Rerun
        next_action: Next action to be taken
        task_status: Completed or Inprogress or Failed or UserFeedback or Rerun
    Returns:
        ActionResult object containing the aggregated results.
    """
    user_goal: str = Field(description="Users overall goal. Don't mark status Completed until completed.")
    think_and_plan: str = Field(description="Step by step thinking and planning of user task")
    execution_plan: str = Field(description="Detailed execution plan of user task and tools needed to execute the task")
    execution_result: str = Field(description="Result of the execution of the user task and status of the execution")
    goal_status: str = Field(description="Completed or Inprogress or Failed or UserFeedback or Rerun")
    next_action: str = Field(description="Next action to be taken")
    task_status: str = Field(description="Completed or Inprogress or Failed or UserFeedback or Rerun")

@cache
def get_superAgent():
    from azure_agent import openai_model
    superAgent = Agent(
        model=openai_model,
        name="SuperAgent",
        system_prompt=SYSTEM_PROMPT,
        result_type=ActionResult,
        retries=3,
        model_settings={"temperature": 0.0}
    )
    return superAgent

superAgent = get_superAgent()

@superAgent.tool_plain
@cache
def run_command(command, shell_preference=None):
    """Execute terminal commands safely with shell control and parse complex outputs.
    shell_preference is the shell to be used. It can be powershell, cmd or default.
    If shell_preference is not provided, then default to powershell.
    If the command fails, then return the environment information and the error message.
    Assume that the command is executed in the current directory.
    Assume Windows is the operating system on first run, unless the user specifies otherwise or the command fails.

    Args:
        command: The command to be executed.
        shell_preference: The shell to be used. It can be powershell, cmd or default.
    Returns:
        The result of the command execution.
    Common Examples:
    - python --version
    - echo %PATH% and shell_preference: cmd
    - dir and shell_preference: cmd

    next_action = "think_and_plan"
    """

    command_markdown = f"Running function run_command with command: {command} and shell_preference: {shell_preference}"
    console.print(Panel(command_markdown, title="Command", border_style="green"))
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
                process: subprocess.CompletedProcess[str] = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True
                )
            elif shell_preference.lower() == 'cmd':
                process: subprocess.CompletedProcess[str] = subprocess.run(
                    args=["cmd", "/c", command],
                    capture_output=True,
                    text=True
                )
            else:
                process: subprocess.CompletedProcess[str] = subprocess.run(
                    args=["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True
                )
        else:
            process: subprocess.CompletedProcess[str] = subprocess.run(
                args=command,
                shell=True,
                capture_output=True,
                text=True
            )

        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["returncode"] = process.returncode

        if process.returncode != 0:
            result["env_check"] = platform.platform()

    except Exception as e:
        result["stderr"] = str(e)
        result["env_check"] = platform.platform()
    console.print(Panel(Table(f"Result: {result['stdout']}, {result['stderr']}, {result['returncode']}, {result['env_check']}", title="Result", border_style="green")))
    return result


def display_aggregated_results(response: ActionResult):
    """Display aggregated task summary results in a concise, well-formatted table once all actions are completed.
    Step 5: display_aggregated_results #Optional
    Args:
        user_goal: Users overall goal. Don't mark status Completed until completed.
        think_and_plan: Step by step thinking and planning of user task
        execution_plan: Detailed execution plan of user task and tools needed to execute the task
        execution_result: Result of the execution of the user task and status of the execution
        goal_status: Completed or Inprogress or Failed or UserFeedback or Rerun
        next_action: Next action to be taken
        task_status: Completed or Inprogress or Failed or UserFeedback or Rerun
        next_action = "think_and_plan"
    """
    print(f"Running function display_aggregated_results")    
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
        result = Markdown(response.execution_result)
        summary_table.add_row("Results: ", result)
    
    if hasattr(response, 'task_status'):
        status_icon = "✓" if response.task_status in ["Completed"] else "⚠"
        summary_table.add_row("Status: ", f"{status_icon} {response.task_status}")
    
    # Display the table
    console.print(summary_table)
    console.print(Panel(f"Task Summary: {response.execution_result}", title="Task Summary", border_style="green"))

    # If there are next steps, display them in a separate panel without recursion
    if hasattr(response, 'next_action') and response.next_action:
        next_steps = Panel(
            Markdown(response.next_action),
            title="Next Steps",
            border_style="blue"
        )
        console.print(next_steps)  # Just print the panel, don't call recursively



@superAgent.tool_plain
def explain_action_plan(response: ActionResult,action_name:str):
    """
    Display Task Plan, Execution Steps, Execution Result, Next Action and Task Status should be headings.
    action_name should be the title of the panel based on the action agent is performing.
    Step 2: explain_action_plan #Mandatory
    next_action = "think_and_plan"
    """
    #Running function explain_action_plan
    print(f"Running function explain_action_plan")
    response_text = (
        f"**Action Name:**\n{action_name}\n\n"
        f"**User Goal:**\n{response.user_goal}\n\n"
        f"**Thinking Plan:**\n{response.think_and_plan}\n\n"
        f"**Executing Plan:**\n{response.execution_plan}\n\n"
        f"**Execution Result:**\n{response.execution_result}\n\n"
        f"**Goal Status:**\n{response.goal_status}\n\n"
        f"**Next Action:**\n{response.next_action}\n\n"
        f"**Task Status:**\n{response.task_status}\n"
    )
    response_markdown = Markdown(response_text)
    console.print(Panel(response_markdown, title=action_name, border_style="green"))


@superAgent.tool_plain
@cache
def think_and_plan(thought: str):
    """I will use this tool to think and plan the user task.
    I will write my thoughts before I execute the task.
    I will examine results of tool call output and reflect on the results.
    Step 1: think_and_plan #Mandatory
    """
    print(f"Running function think_and_plan")
    console.print(Panel(f"## Thinking\n{thought}", title="Thinking", border_style="green"))

@superAgent.tool_plain
@cache
def message_user(message: str):
    """
    Explain the task status and the next action to the user.
    Do not wait for user feedback.
    Step 6: message_user #Optional
    next_action = "think_and_plan"
    """
    print(f"Running function message_user")
    console.print(Panel(f"## Message User\n{message}", title="Message User", border_style="green"))
    

# Define API URL
api_url = "http://localhost:8000"

# Function to store messages

async def store_message(user_email, question, category, answer):
    payload = {
        "user_email": user_email,
        "question": question,
        "category": category,
        "answer": answer
    }
    response: requests.Response = requests.post(f"{api_url}/store", json=payload)
    return response.json()

# Function to retrieve relevant messages
async def retrieve_relevant(user_email, question, k=5):
    payload = {
        "user_email": user_email,
        "question": question,
        "k": k
    }
    response: requests.Response = requests.post(f"{api_url}/retrieve", json=payload)
    return response.json()

# Function to summarize messages
async def summarize_messages(user_email, question, k=5):
    payload = {
        "user_email": user_email,
        "question": question,
        "k": k
    }
    response: requests.Response = requests.post(f"{api_url}/summarize", json=payload)
    return response.json()

# Modify process_tasks to include error handling and API calls
@superAgent.tool_plain
async def process_tasks(message, message_history) -> RunResult[ActionResult] | str:
    print(f"Running function process_tasks")
    while True:
        try:
            console.print(Panel(f"User: {message}", title="User", border_style="green"))

            # Store the initial message
            await store_message(user_email, message, "User Input", "")

            if message_history:
                response: RunResult[ActionResult] = await superAgent.run(
                    user_prompt=message,
                    message_history=message_history
                )
            else:
                response: RunResult[ActionResult] = await superAgent.run(
                    user_prompt=message,
                )

            if isinstance(response.data, ActionResult):
                explain_action_plan(response=response.data, action_name=response.data.next_action)
                display_aggregated_results(response=response.data)
                if response.data.task_status in ["Completed"]:
                    return response
                elif response.data.task_status in ["UserFeedback"]:
                    return response
                elif response.data.task_status in ["Failed"]:
                    # Summarize the error and get enhanced query
                    summary_response = await summarize_messages(user_email, response.data.execution_result)
                    console.print(Panel(summary_response['summary'], title="Error Summary", border_style="red"))
                    message = summary_response['enhanced_question'] + " Rerun"
                else:
                    message = response.data.next_action
                    console.print(Panel(message, title="Next Action", border_style="green"))
                    continue
            elif isinstance(response.data, str):
                console.print(Panel(response.data, title="ResultStr", border_style="green"))
                return response
            else:
                response.data.next_action = "think_and_plan"
                console.print(Panel(f"Unexpected response type: {type(response.data)}", title="Error", border_style="red"))
                continue

        except Exception as e:
            # Log the error and summarize
            await store_message(user_email, message, "Error", str(e))
            summary_response = await summarize_messages(user_email, str(e))
            console.print(Panel(f"Exception in process_tasks: {str(e)}", title="Error", border_style="red"))
            console.print(Panel(summary_response['summary'], title="Error Summary", border_style="red"))
            return f"Exception in process_tasks: {str(e)}"


async def cli_mode():
    """CLI interface for interacting with the agent."""
    global message_history
    welcome_text = """
        # CLI Mode Initialized

        Type 'exit' or 'quit' to stop.

        ## Available Commands
        - Any text: Process as a task
        - exit/quit: Exit the program
        """
    console.print(Panel(welcome_text, title="Welcome", border_style="green"))
    
    

    while True:
        try:
            user_input = input("> ").strip()

            if user_input.lower() in ["exit", "quit"]:
                console.print(Panel("## Exiting CLI mode", title="Success", border_style="green"))
                break

            result = await process_tasks(
                message=user_input, message_history=message_history)                
            # Parse tool calls from the response and update message_history
            # if isinstance(result, RunResult):
            #     message_history = result.all_messages()
            #     #console.print(Panel(result.data.execution_result, title="RunResult", border_style="green"))
            #     #explain_action_plan(response=result.data,action_name=result.data.next_action)
            # elif isinstance(result, ActionResult):
            #     console.print(Panel("Session Completed", title="Session Completed", border_style="green"))
            #     # Don't append strings to message_history since it expects ModelMessage objects
            #     #console.print(Panel(result, title="ActionResult", border_style="green"))
            # elif isinstance(result, str):
            #     console.print(Panel(result, title="ResultStr", border_style="green"))
            if isinstance(result, str) and "Exception" in result:
                # Format error message nicely
                error_panel = Panel(
                    Markdown(f"**Error**: {result}"),
                    title="Error",
                    border_style="red"
                )
                console.print(error_panel)
            
        except KeyboardInterrupt:
            #logit.log_message("## KeyboardInterrupt - Exiting", level="warning")
            break
            
        except Exception as e:
            error_panel = Panel(
                Markdown(f"**Error**: {str(e)}"),
                title="Unexpected Error",
                border_style="red"
            )
            console.print(error_panel)
            break

if __name__ == "__main__":
    asyncio.run(cli_mode())