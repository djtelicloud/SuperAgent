# SuperAgent Terminal UI & Color Coding — Complete Architecture Report

> **Purpose**: This document is a comprehensive, self-contained reference for reproducing the SuperAgent terminal UI in a new project. It is designed to be used directly as an LLM prompt or blueprint. Every pattern, color choice, component, and design decision is documented with code examples.

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Console Setup & Configuration](#2-console-setup--configuration)
3. [Color Coding System](#3-color-coding-system)
4. [Panel System — The Primary Display Unit](#4-panel-system--the-primary-display-unit)
5. [Table System — Structured Data Display](#5-table-system--structured-data-display)
6. [Markdown Rendering](#6-markdown-rendering)
7. [Status Icons & Visual Indicators](#7-status-icons--visual-indicators)
8. [Display Functions Architecture](#8-display-functions-architecture)
9. [Custom Theme System (Extended)](#9-custom-theme-system-extended)
10. [CustomPrint Class — Unified Display Manager](#10-customprint-class--unified-display-manager)
11. [Error Display Patterns](#11-error-display-patterns)
12. [Progress Indicators](#12-progress-indicators)
13. [Logging Integration](#13-logging-integration)
14. [Code Syntax Highlighting & Diffs](#14-code-syntax-highlighting--diffs)
15. [CLI Welcome & Prompt Flow](#15-cli-welcome--prompt-flow)
16. [Complete LLM Prompt for Recreating This UI](#16-complete-llm-prompt-for-recreating-this-ui)

---

## 1. Technology Stack

| Component | Package | Version | Purpose |
|-----------|---------|---------|---------|
| Terminal UI | `rich` | 13.9.4 | All terminal rendering: panels, tables, markdown, syntax highlighting, progress bars, themes |
| Data Models | `pydantic` | 2.10.4 | Structured response models that feed into display functions |
| AI Agent | `pydantic-ai` | 0.0.15 | Agent framework whose tool outputs are displayed via rich |
| Python | Python | 3.10+ | Runtime |

### Key Rich Imports Used

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.pretty import Pretty
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.theme import Theme
from rich import print  # Enhanced print
```

---

## 2. Console Setup & Configuration

### Basic Console (Used in Production)

```python
from rich.console import Console

console = Console(record=True)
```

- **`record=True`**: Enables capturing all output for later export via `console.export_text()` or `console.export_html()`. This is essential for logging terminal output to files or sending it over APIs.

### Themed Console (Extended System)

```python
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "code": "blue",
    "azure_blue": "#0078D4",  # Azure brand blue
    "ml_blue": "#00A4EF"      # ML brand blue
})

console = Console(theme=custom_theme, record=True)
```

This creates semantic color names that can be used throughout the application as `style="info"`, `style="error"`, etc.

---

## 3. Color Coding System

### Border Color Conventions

| Context | Border Style | Meaning |
|---------|-------------|---------|
| Success / Normal Output | `"green"` | Everything is working, informational display |
| Error / Exception | `"red"` | Something went wrong |
| Data Tables / Results | `"blue"` | Structured data, summaries, next steps |
| Code Diffs | `"azure_blue"` (`#0078D4`) | Azure-branded code changes |

### Text Style Conventions

| Element | Style | Usage |
|---------|-------|-------|
| Table headers | `"bold magenta"` | Column headers in data tables |
| Metric/label column | `"cyan"` | Left column in key-value tables |
| Value column | `"green"` | Right column in key-value tables |
| Status column | `"yellow"` | Status indicators |
| Code blocks | `"blue"` | Code-related content |
| Success indicators | `"green"` | `✓ Success`, `✓ Completed` |
| Failure indicators | `"red"` | `✗ Failed`, errors |

### Inline Rich Markup

```python
# Success with green
table.add_row("Status", "[green]✓ Success[/green]")

# Failure with red
table.add_row("Status", "[red]✗ Failed[/red]")

# Dynamic status styling
status_style = "green" if success else "red"
table.add_row("Status", f"[{status_style}]{status_icon} {'Success' if success else 'Failed'}[/{status_style}]")
```

---

## 4. Panel System — The Primary Display Unit

Panels are the **core visual element** of SuperAgent's UI. Every piece of information is wrapped in a Panel with a descriptive title and color-coded border.

### Panel Anatomy

```python
from rich.panel import Panel
from rich.markdown import Markdown

console.print(Panel(
    content,           # str, Markdown, Table, Syntax, or any Rich renderable
    title="Title",     # Appears at top of panel border
    border_style="green"  # Color of the panel border
))
```

### Panel Usage Patterns

#### 1. Command Execution Panel

```python
command_markdown = f"Running function run_command with command: {command} and shell_preference: {shell_preference}"
console.print(Panel(command_markdown, title="Command", border_style="green"))
```

#### 2. Thinking/Planning Panel

```python
console.print(Panel(f"## Thinking\n{thought}", title="Thinking", border_style="green"))
```

#### 3. User Message Panel

```python
console.print(Panel(f"## Message User\n{message}", title="Message User", border_style="green"))
```

#### 4. User Input Panel

```python
console.print(Panel(f"User: {message}", title="User", border_style="green"))
```

#### 5. Action Plan Panel (with Markdown)

```python
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
```

#### 6. Error Panel

```python
error_panel = Panel(
    Markdown(f"**Error**: {str(e)}"),
    title="Unexpected Error",
    border_style="red"
)
console.print(error_panel)
```

#### 7. Error Summary Panel

```python
console.print(Panel(summary_response['summary'], title="Error Summary", border_style="red"))
```

#### 8. Next Action Panel

```python
console.print(Panel(message, title="Next Action", border_style="green"))
```

#### 9. Next Steps Panel (with Markdown)

```python
next_steps = Panel(
    Markdown(response.next_action),
    title="Next Steps",
    border_style="blue"
)
console.print(next_steps)
```

#### 10. Welcome Panel

```python
welcome_text = """
    # CLI Mode Initialized

    Type 'exit' or 'quit' to stop.

    ## Available Commands
    - Any text: Process as a task
    - exit/quit: Exit the program
    """
console.print(Panel(welcome_text, title="Welcome", border_style="green"))
```

#### 11. Result Panel with Embedded Table

```python
console.print(Panel(Table(
    f"Result: {result['stdout']}, {result['stderr']}, {result['returncode']}, {result['env_check']}",
    title="Result",
    border_style="green"
)))
```

#### 12. Session/Exit Panel

```python
console.print(Panel("## Exiting CLI mode", title="Success", border_style="green"))
```

### Panel Title Naming Convention

| Title | When Used |
|-------|-----------|
| `"Command"` | Before running a shell command |
| `"Thinking"` | Agent's internal thought process |
| `"Message User"` | Agent communicating to user |
| `"User"` | Displaying user input |
| `"{action_name}"` | Dynamic: current action being performed |
| `"Error"` | Error messages |
| `"Error Summary"` | AI-summarized error analysis |
| `"Unexpected Error"` | Unhandled exceptions |
| `"Model Error"` | LLM-specific errors |
| `"Next Action"` | What the agent will do next |
| `"Next Steps"` | Detailed next steps |
| `"Task Summary"` | Summary of completed task |
| `"Result"` | Command execution result |
| `"ResultStr"` | String-type responses |
| `"Welcome"` | CLI initialization |
| `"Success"` | Successful completion |
| `"Tool Call: {name}"` | Tool execution display |

---

## 5. Table System — Structured Data Display

### Task Summary Table

```python
summary_table = Table(
    title="Task Summary",
    show_header=True,
    header_style="bold magenta",
    border_style="blue"
)

summary_table.add_column("Metric", style="cyan")
summary_table.add_column("Value", style="green")

# Add result row with Markdown rendering
result = Markdown(response.execution_result)
summary_table.add_row("Results: ", result)

# Add status row with icon
status_icon = "✓" if response.task_status in ["Completed"] else "⚠"
summary_table.add_row("Status: ", f"{status_icon} {response.task_status}")

console.print(summary_table)
```

### Tool Usage Summary Table

```python
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
```

### Tool Call Detail Table

```python
table = Table(
    title=f"Tool Call: {tool_name}",
    show_header=True,
    header_style="bold magenta",
    border_style="blue"
)
table.add_column("Parameter", style="cyan")
table.add_column("Value", style="green")

table.add_row("Input", str(input_data))
table.add_row("Output", str(output_data))

# Dynamic status coloring
status_icon = "✓" if success else "✗"
status_style = "green" if success else "red"
table.add_row("Status", f"[{status_style}]{status_icon} {'Success' if success else 'Failed'}[/{status_style}]")

console.print(table)
```

### Test Results Table

```python
table = Table(title=f"Test Results for {tool_name}")
table.add_column("Test #", style="cyan")
table.add_column("Input", style="magenta")
table.add_column("Output", style="green")
table.add_column("Status", style="yellow")

for i, result in enumerate(test_results, 1):
    table.add_row(
        str(i),
        str(result.get('input', '')),
        str(result.get('output', '')),
        '✓' if result.get('success', False) else '✗'
    )
```

### Status/Environment Table

```python
table = Table(show_header=True, header_style="bold blue")
table.add_column("Component")
table.add_column("Status")

for key, value in items.items():
    table.add_row(key, str(value))

console.print(table)
```

### Table Design Rules

1. **Always use `show_header=True`** for readability
2. **`header_style="bold magenta"`** is the standard header style for data tables
3. **`border_style="blue"`** for data tables; `"green"` for result panels
4. **Left column** is always `style="cyan"` (labels/metrics)
5. **Right column** is always `style="green"` (values)
6. **Status columns** use `style="yellow"` or inline markup for dynamic coloring

---

## 6. Markdown Rendering

Rich's `Markdown` class is used extensively for formatting content inside panels.

### Markdown Inside Panels

```python
from rich.markdown import Markdown

# Agent action plan with bold headers
response_text = (
    f"**Action Name:**\n{action_name}\n\n"
    f"**User Goal:**\n{response.user_goal}\n\n"
    f"**Thinking Plan:**\n{response.think_and_plan}\n\n"
)
console.print(Panel(Markdown(response_text), title="Plan", border_style="green"))
```

### Markdown in Error Messages

```python
error_panel = Panel(
    Markdown(f"**Error**: {str(e)}"),
    title="Error",
    border_style="red"
)
console.print(error_panel)
```

### Markdown in Table Cells

```python
# Rich allows Markdown objects as table cell values
result = Markdown(response.execution_result)
summary_table.add_row("Results: ", result)
```

### Auto-Detection of Markdown Content

```python
def display_message(self, message: str, style: str = "info") -> None:
    # Auto-detect markdown markers
    if any(marker in message for marker in ["##", "**", "`", "```"]):
        self._console.print(Markdown(message))
        return
    # Auto-detect Python code
    if message.lstrip().startswith(("def ", "class ", "import ", "from ")):
        syntax = Syntax(message, "python", theme="monokai")
        self._console.print(Panel(syntax, title="Code", border_style="blue"))
        return
    # Plain message
    self._console.print(message, style=style)
```

---

## 7. Status Icons & Visual Indicators

| Icon | Meaning | Context |
|------|---------|---------|
| `✓` | Success / Completed | Task status, tool results |
| `✗` | Failed | Tool failures, test failures |
| `⚠` | In Progress / Warning | Non-completed task states |

### Status Mapping Logic

```python
# Task status icons
status_icon = "✓" if response.task_status in ["Completed"] else "⚠"

# Tool result icons
status_icon = "✓" if success else "✗"

# Test result icons
'✓' if result.get('success', False) else '✗'
```

### Status Colors

```python
# Logging level to color mapping
style_map = {
    "error": "red",
    "warning": "yellow",
    "success": "green",
    "info": "blue"
}
```

---

## 8. Display Functions Architecture

### `display_aggregated_results(response: ActionResult)`

The main results display function. Shows a summary table + optional next steps panel.

```python
def display_aggregated_results(response: ActionResult):
    # 1. Create summary table with "Task Summary" title
    summary_table = Table(
        title="Task Summary",
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    # 2. Add execution result as Markdown
    if hasattr(response, 'execution_result'):
        result = Markdown(response.execution_result)
        summary_table.add_row("Results: ", result)

    # 3. Add status with icon
    if hasattr(response, 'task_status'):
        status_icon = "✓" if response.task_status in ["Completed"] else "⚠"
        summary_table.add_row("Status: ", f"{status_icon} {response.task_status}")

    # 4. Display the table
    console.print(summary_table)

    # 5. Task summary panel
    console.print(Panel(
        f"Task Summary: {response.execution_result}",
        title="Task Summary",
        border_style="green"
    ))

    # 6. Next steps in blue panel with Markdown
    if hasattr(response, 'next_action') and response.next_action:
        next_steps = Panel(
            Markdown(response.next_action),
            title="Next Steps",
            border_style="blue"
        )
        console.print(next_steps)
```

### `explain_action_plan(response: ActionResult, action_name: str)`

Displays the full agent reasoning in a single structured Markdown panel.

```python
def explain_action_plan(response: ActionResult, action_name: str):
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
```

### `think_and_plan(thought: str)`

Simple thinking display.

```python
def think_and_plan(thought: str):
    console.print(Panel(f"## Thinking\n{thought}", title="Thinking", border_style="green"))
```

### `message_user(message: str)`

User-facing message display.

```python
def message_user(message: str):
    console.print(Panel(f"## Message User\n{message}", title="Message User", border_style="green"))
```

### `enhanced_parse_and_display_tool_call_results(...)`

Rich table for individual tool call results.

```python
def enhanced_parse_and_display_tool_call_results(tool_name, input_data, output_data, success):
    table = Table(
        title=f"Tool Call: {tool_name}",
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="green")

    if input_data:
        formatted_input = format_as_markdown(input_data)
        if formatted_input.strip():
            table.add_row("Input", formatted_input)

    if output_data:
        formatted_output = format_as_markdown(output_data)
        if formatted_output.strip():
            table.add_row("Output", formatted_output)

    status_icon = "✓" if success else "✗"
    status_style = "green" if success else "red"
    table.add_row("Status", f"[{status_style}]{status_icon} {'Success' if success else 'Failed'}[/{status_style}]")

    console.print(table)
```

---

## 9. Custom Theme System (Extended)

The extended theme system enables semantic styling throughout the application.

```python
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",        # Informational messages
    "warning": "yellow",   # Warnings
    "error": "red",        # Errors
    "success": "green",    # Success messages
    "code": "blue",        # Code-related content
    "azure_blue": "#0078D4",  # Azure brand color
    "ml_blue": "#00A4EF"      # ML/AI brand color
})

console = Console(theme=custom_theme, record=True)
```

### Usage Examples

```python
console.print("Operation completed", style="success")
console.print("Check your configuration", style="warning")
console.print("Connection failed", style="error")
console.print("Processing request...", style="info")
```

---

## 10. CustomPrint Class — Unified Display Manager

A Pydantic-based class that handles all display logic with type auto-detection.

```python
from pydantic import BaseModel, PrivateAttr

class CustomPrint(BaseModel):
    _console: Console = PrivateAttr(
        default_factory=lambda: Console(theme=custom_theme, record=True)
    )

    def display(self, data: Any, context: Optional[dict] = None) -> None:
        """Auto-detect data type and display appropriately."""
        if isinstance(data, str):
            self.display_message(data)
        elif isinstance(data, dict):
            self.create_status_table(data)
        elif hasattr(data, 'dict'):
            self.display_message(str(data.dict()))
        elif isinstance(data, int):
            self.display_message(str(data))
        else:
            self._console.print(
                f"Unsupported data type: {type(data).__name__}",
                style="warning"
            )

    def display_message(self, message: str, style: str = "info") -> None:
        """Smart message display with auto-detection."""
        # Markdown detection
        if any(marker in message for marker in ["##", "**", "`", "```"]):
            self._console.print(Markdown(message))
            return
        # Python code detection
        if message.lstrip().startswith(("def ", "class ", "import ", "from ")):
            syntax = Syntax(message, "python", theme="monokai")
            self._console.print(Panel(syntax, title="Code", border_style="blue"))
            return
        # Azure style mapping
        if style == "azure":
            style = "azure_blue"
        # Regular message
        self._console.print(message, style=style)

    def create_status_table(self, items: dict) -> None:
        """Key-value table with blue headers."""
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Component")
        table.add_column("Status")
        for key, value in items.items():
            table.add_row(key, str(value))
        self._console.print(table)

    def display_code_diff(self, original: str, modified: str, title: str = "Code Changes") -> None:
        """Side-by-side diff with syntax highlighting."""
        from difflib import unified_diff
        diff = list(unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="Original",
            tofile="Modified"
        ))
        if diff:
            diff_text = "".join(diff)
            self._console.print(Panel(
                Syntax(diff_text, "diff", theme="monokai"),
                title=title,
                border_style="azure_blue"
            ))
        else:
            self._console.print("No changes detected", style="warning")

    def get_formatted_output(self) -> str:
        """Export captured output as text."""
        return self._console.export_text()

    def clear_output(self) -> None:
        """Reset console buffer."""
        self._console = Console(theme=custom_theme, record=True)
```

---

## 11. Error Display Patterns

### Simple Error

```python
console.print(Panel(
    Markdown(f"**Error**: {str(e)}"),
    title="Error",
    border_style="red"
))
```

### Model/LLM Error

```python
console.print(Panel(
    Markdown(f"**Model Error**: {str(e)}"),
    title="Model Error",
    border_style="red"
))
```

### Unexpected Error

```python
console.print(Panel(
    Markdown(f"**Error**: {str(e)}"),
    title="Unexpected Error",
    border_style="red"
))
```

### Error Summary (AI-Generated)

```python
console.print(Panel(
    summary_response['summary'],
    title="Error Summary",
    border_style="red"
))
```

### Exception in Processing

```python
console.print(Panel(
    f"Exception in process_tasks: {str(e)}",
    title="Error",
    border_style="red"
))
```

### Unexpected Type Error

```python
console.print(Panel(
    f"Unexpected response type: {type(response.data)}",
    title="Error",
    border_style="red"
))
```

### Structured Error Report (Logging)

```python
def format_error(self, error: Exception, context: Any = None) -> str:
    error_text = f"""
## Error Details
**Type:** {type(error).__name__}
**Error:** {str(error)}"""
    if context:
        error_text += f"\n**Context:** {context}"
    return error_text
```

### Error Analysis Display

```python
debug_response = (
    "## Error Analysis\n"
    f"**Error:** {error}\n"
    f"**Context:** {context_str}\n\n"
    "### Suggested Fixes:\n"
    + "\n".join(f"- {fix}" for fix in fixes)
    + "\n\n"
    f"### Environment Check:\n"
    f"- Running in: {self.debug_context['environment']}\n"
    f"- Error count: {self.debug_context['error_count']}\n"
    f"- Active fixes: {self.debug_context['active_fixes']}\n\n"
    "### Next Steps:\n"
    "1. Review suggested fixes\n"
    "2. Apply any relevant solutions\n"
    "3. Verify environment configuration\n"
    "4. Review error history for patterns\n"
)
customPrint.display_message(debug_response, style="error")
```

---

## 12. Progress Indicators

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

def display_progress(message: str) -> Progress:
    """Create a spinner-based progress indicator."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )
    progress.add_task(description=message, total=None)
    return progress
```

---

## 13. Logging Integration

### Log Message with Panel

```python
def log_message(self, message: str, level: str = "info", log: bool = True, print_msg: bool = True):
    style_map = {
        "error": "red",
        "warning": "yellow",
        "success": "green",
        "info": "blue"
    }

    # Auto-detect tables vs markdown
    if "╭" in message or "├" in message:
        console.print(message)  # Rich table characters - print directly
    else:
        md = Markdown(message, style="default")
        console.print(Panel(
            md,
            title=level.title(),   # "Info", "Error", "Warning", "Success"
            border_style=style_map[level]
        ))
```

### Logging Setup with Rich Handler

```python
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(filename=log_file, mode="a"),
        logging.StreamHandler(stream=sys.stdout)
    ]
)
```

---

## 14. Code Syntax Highlighting & Diffs

### Python Code Display

```python
from rich.syntax import Syntax

syntax = Syntax(code_string, "python", theme="monokai")
console.print(Panel(syntax, title="Code", border_style="blue"))
```

### Unified Diff Display

```python
from difflib import unified_diff

diff = list(unified_diff(
    original.splitlines(keepends=True),
    modified.splitlines(keepends=True),
    fromfile="Original",
    tofile="Modified"
))
if diff:
    diff_text = "".join(diff)
    console.print(Panel(
        Syntax(diff_text, "diff", theme="monokai"),
        title="Code Changes",
        border_style="azure_blue"  # #0078D4
    ))
```

---

## 15. CLI Welcome & Prompt Flow

### Startup Sequence

```python
async def cli_mode():
    welcome_text = """
        # CLI Mode Initialized

        Type 'exit' or 'quit' to stop.

        ## Available Commands
        - Any text: Process as a task
        - exit/quit: Exit the program
        """
    console.print(Panel(welcome_text, title="Welcome", border_style="green"))

    while True:
        user_input = input("> ").strip()

        if user_input.lower() in ["exit", "quit"]:
            console.print(Panel("## Exiting CLI mode", title="Success", border_style="green"))
            break

        # Process and display results...
```

### Visual Flow

```
┌─────────────────────────────────┐
│         Welcome (green)         │  ← Panel: CLI initialization
│  # CLI Mode Initialized        │
│  Type 'exit' or 'quit' to stop │
└─────────────────────────────────┘

> user types a command

┌─────────────────────────────────┐
│          User (green)           │  ← Panel: Echo user input
│  User: {user_input}            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│        Thinking (green)         │  ← Panel: Agent thinking
│  ## Thinking                    │
│  {internal reasoning}           │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│      Message User (green)       │  ← Panel: Agent→User message
│  ## Message User                │
│  {explanation of approach}      │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│     {Action Name} (green)       │  ← Panel: Full action plan
│  **Action Name:** ...           │
│  **User Goal:** ...             │
│  **Thinking Plan:** ...         │
│  **Executing Plan:** ...        │
│  **Execution Result:** ...      │
│  **Goal Status:** ...           │
│  **Next Action:** ...           │
│  **Task Status:** ...           │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│       Command (green)           │  ← Panel: Command being run
│  Running function run_command   │
│  with command: {cmd}            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│        Result (green)           │  ← Panel+Table: Command output
│  ┌──────────────────────────┐   │
│  │ Result: stdout, stderr,  │   │
│  │ returncode, env_check    │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘

╔═════════════════════════════════╗
║     Task Summary (blue)         ║  ← Table: Final summary
╠════════════╦════════════════════╣
║ Metric     ║ Value              ║  header: bold magenta
╠════════════╬════════════════════╣
║ Results:   ║ {execution_result} ║  cyan    green
║ Status:    ║ ✓ Completed        ║  cyan    green
╚════════════╩════════════════════╝

┌─────────────────────────────────┐
│     Task Summary (green)        │  ← Panel: Task summary text
│  Task Summary: {result}         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│      Next Steps (blue)          │  ← Panel: What comes next
│  {next_action as markdown}      │
└─────────────────────────────────┘
```

---

## 16. Complete LLM Prompt for Recreating This UI

Use the following prompt with any LLM to recreate the SuperAgent terminal UI in a new Python project:

---

### 🤖 LLM PROMPT — Recreate SuperAgent Terminal UI

```
You are building a Python CLI application with a rich, beautiful terminal UI. Use the `rich` library (version 13.9+) for all terminal rendering.

## SETUP

Install: pip install rich pydantic

Initialize the console:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.theme import Theme
    from rich.progress import Progress, SpinnerColumn, TextColumn

    custom_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "code": "blue",
    })
    console = Console(theme=custom_theme, record=True)

## DESIGN PRINCIPLES

1. **Everything is a Panel**: Wrap all output in `Panel()` with a descriptive `title` and color-coded `border_style`.
2. **Green borders = normal/success**: Use `border_style="green"` for informational output, user messages, thinking, commands, results.
3. **Red borders = errors**: Use `border_style="red"` for all error displays.
4. **Blue borders = data/structure**: Use `border_style="blue"` for tables, next steps, structured summaries.
5. **Markdown everywhere**: Use `Markdown()` for any content that has bold, headers, lists, or code blocks.
6. **Tables for key-value data**: Use `Table()` with `header_style="bold magenta"`, `border_style="blue"`, left column `style="cyan"`, right column `style="green"`.
7. **Status icons**: Use `✓` for success/completed, `✗` for failed, `⚠` for in-progress/warning.
8. **Dynamic color in cells**: Use inline markup like `[green]✓ Success[/green]` and `[red]✗ Failed[/red]`.

## DISPLAY FUNCTIONS TO IMPLEMENT

### 1. Welcome Screen
    def show_welcome():
        text = "# My App\nType 'exit' to quit.\n## Commands\n- Any text: process\n- exit: quit"
        console.print(Panel(text, title="Welcome", border_style="green"))

### 2. User Input Echo
    def show_user_input(message):
        console.print(Panel(f"User: {message}", title="User", border_style="green"))

### 3. Thinking/Reasoning Display
    def show_thinking(thought):
        console.print(Panel(f"## Thinking\n{thought}", title="Thinking", border_style="green"))

### 4. Action Plan Display
    def show_action_plan(plan_dict, title="Action Plan"):
        text = "\n\n".join(f"**{k}:**\n{v}" for k, v in plan_dict.items())
        console.print(Panel(Markdown(text), title=title, border_style="green"))

### 5. Command Execution Display
    def show_command(command):
        console.print(Panel(f"Running: {command}", title="Command", border_style="green"))

### 6. Results Summary Table
    def show_results(result_text, status, next_action=None):
        table = Table(title="Task Summary", show_header=True, header_style="bold magenta", border_style="blue")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Results", Markdown(result_text))
        icon = "✓" if status == "Completed" else "⚠"
        table.add_row("Status", f"{icon} {status}")
        console.print(table)
        if next_action:
            console.print(Panel(Markdown(next_action), title="Next Steps", border_style="blue"))

### 7. Error Display
    def show_error(error_msg, title="Error"):
        console.print(Panel(Markdown(f"**Error**: {error_msg}"), title=title, border_style="red"))

### 8. Tool Call Results Table
    def show_tool_result(tool_name, input_data, output_data, success):
        table = Table(title=f"Tool Call: {tool_name}", show_header=True, header_style="bold magenta", border_style="blue")
        table.add_column("Component", style="cyan")
        table.add_column("Details", style="green")
        table.add_row("Input", str(input_data))
        table.add_row("Output", str(output_data))
        icon = "✓" if success else "✗"
        color = "green" if success else "red"
        table.add_row("Status", f"[{color}]{icon} {'Success' if success else 'Failed'}[/{color}]")
        console.print(table)

### 9. Code Display with Syntax Highlighting
    def show_code(code, language="python"):
        syntax = Syntax(code, language, theme="monokai")
        console.print(Panel(syntax, title="Code", border_style="blue"))

### 10. Progress Spinner
    def create_progress(message):
        progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console)
        progress.add_task(description=message, total=None)
        return progress

## CLI LOOP PATTERN
    async def main():
        show_welcome()
        while True:
            user_input = input("> ").strip()
            if user_input.lower() in ["exit", "quit"]:
                console.print(Panel("## Goodbye!", title="Success", border_style="green"))
                break
            show_user_input(user_input)
            show_thinking("Analyzing the request...")
            # Process and display results...

## KEY VISUAL RULES
- Every distinct piece of information gets its own Panel
- Panels flow vertically in the terminal, creating a clean timeline
- Use Markdown inside panels for rich formatting (bold, headers, lists)
- Tables are reserved for structured key-value or multi-column data
- Errors always stand out with red borders
- The visual hierarchy: Panel (container) > Table (structured data) > Markdown (formatted text)
- Console recording (record=True) enables output export for logging
```

---

## Summary of Key Design Decisions

1. **Panel-first architecture**: Every piece of information is wrapped in a bordered Panel, creating clear visual separation and a timeline-like flow.
2. **Semantic color coding**: Green=success/normal, Red=error, Blue=data/structure, Cyan=labels, Magenta=headers.
3. **Markdown integration**: Content inside panels uses rich Markdown for formatting, enabling bold text, headers, lists, and code blocks.
4. **Table standardization**: All tables follow the same style: `bold magenta` headers, `blue` borders, `cyan` labels, `green` values.
5. **Unicode status icons**: `✓`, `✗`, and `⚠` provide instant visual status recognition.
6. **Output recording**: `Console(record=True)` captures all rendered output for export to logs, files, or APIs.
7. **Auto-detection**: Content type is auto-detected (markdown, code, table, plain text) and rendered appropriately.
8. **Consistent naming**: Panel titles follow a clear taxonomy (Command, Thinking, User, Error, Task Summary, etc.).
