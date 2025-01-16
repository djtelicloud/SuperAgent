# from rich.console import Console
# from rich.markdown import Markdown
# from rich.syntax import Syntax
# from rich.panel import Panel
# from rich.table import Table
# from rich.progress import Progress, SpinnerColumn, TextColumn
# from rich.text import Text
# from rich.pretty import Pretty
# from rich import print
# from rich.logging import RichHandler
# from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
# from rich.highlighter import ReprHighlighter
# from typing import Optional, Any
# from pydantic import BaseModel, PrivateAttr
# from rich.theme import Theme
# # Configure custom theme
# custom_theme = Theme({
#     "info": "cyan",
#     "warning": "yellow",
#     "error": "red",
#     "success": "green",
#     "code": "blue",
#     "azure_blue": "#0078D4",  # Azure blue
#     "ml_blue": "#00A4EF"      # ML blue
# })
# # Global console with recording enabled
# console = Console(theme=custom_theme, record=True)

# class CustomPrint(BaseModel):
#     """Superclass to handle various display formats."""
    
#     # Instance console with recording enabled
#     _console: Console = PrivateAttr(default_factory=lambda: Console(theme=custom_theme, record=True))

#     def display(self, data: Any, context: Optional[dict] = None) -> None:
#         """Display data based on its type."""
#         if isinstance(data, str):
#             self.display_message(data)
#         elif isinstance(data, dict):
#             self.create_status_table(data)
#         elif hasattr(data, 'dict'):
#             self.display_message(str(data.dict()))
#         elif isinstance(data, int):
#             self.display_message(str(data))
#         else:
#             self._console.print(f"Unsupported data type: {type(data).__name__}", style="warning")

#     def display_message(self, message: str, style: str = "info") -> None:
#         """Display a message with proper formatting."""
#         try:
#             # Check if message is markdown
#             if any(marker in message for marker in ["##", "**", "`", "```"]):
#                 self._console.print(Markdown(message))
#                 return
            
#             # Check if message is code
#             if message.lstrip().startswith(("def ", "class ", "import ", "from ")):
#                 syntax = Syntax(message, "python", theme="monokai")
#                 self._console.print(Panel(syntax, title="Code", border_style="blue"))
#                 return
            
#             # Map azure style to azure_blue
#             if style == "azure":
#                 style = "azure_blue"
            
#             # Regular message
#             self._console.print(message, style=style)
            
#         except Exception as e:
#             self._console.print(message)  # Fallback to plain print

#     def create_status_table(self, items: dict) -> None:
#         """Create and display a status table."""
#         table = Table(show_header=True, header_style="bold blue")
#         table.add_column("Component")
#         table.add_column("Status")
        
#         for key, value in items.items():
#             table.add_row(key, str(value))
        
#         self._console.print(table)

#     def display_code_diff(self, original: str, modified: str, title: str = "Code Changes") -> None:
#         """Display code differences."""
#         from difflib import unified_diff
        
#         diff = list(unified_diff(
#             original.splitlines(keepends=True),
#             modified.splitlines(keepends=True),
#             fromfile="Original",
#             tofile="Modified"
#         ))
        
#         if diff:
#             diff_text = "".join(diff)
#             self._console.print(Panel(
#                 Syntax(diff_text, "diff", theme="monokai"),
#                 title=title,
#                 border_style="azure_blue"  # Use azure_blue instead of azure
#             ))
#         else:
#             self._console.print("No changes detected", style="warning")

#     def get_formatted_output(self) -> str:
#         """Return the formatted console output as a string."""
#         try:
#             return self._console.export_text()
#         except AssertionError:
#             # If recording wasn't enabled, create a new console with recording
#             temp_console = Console(theme=custom_theme, record=True)
#             return temp_console.export_text()

#     def clear_output(self) -> None:
#         """Clear the console output buffer."""
#         self._console = Console(theme=custom_theme, record=True)

# def print_welcome() -> None:
#     """Display welcome message."""
#     welcome_text = """
# # Azure-Enhanced Coding Assistant

# Welcome to your AI-powered Azure development companion!
# This assistant helps you with Azure development, ML operations, and RAG systems.

# ## Capabilities:
# - Azure resource deployment
# - ML operations and experiment tracking
# - RAG system development
# - Code generation and review

# Type 'help' for available commands or 'exit' to quit.
# """
#     console.print(Markdown(welcome_text))

# def print_prompt(message: Optional[str] = None) -> None:
#     """Display interactive prompt."""
#     if message:
#         console.print(f"\n{message}")
#     console.print("\n> ", end="")

# def display_progress(message: str) -> Progress:
#     """Create and return a progress indicator."""
#     progress = Progress(
#         SpinnerColumn(),
#         TextColumn("[progress.description]{task.description}"),
#         console=console
#     )
#     progress.add_task(description=message, total=None)
#     return progress




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

# if __name__ == "__main__":
#     print_welcome()
#     print_prompt()
#     #tests
#     customPrint = CustomPrint()
#     customPrint.display_message("Hello, World!")
#     customPrint.create_status_table({"Status": "Success"})
#     customPrint.display_code_diff("print('Hello, World!')", "print('Hello, Azure!')")
#     customPrint.display("Hello, Azure!")
#     customPrint.display({"Status": "Success"})
#     customPrint.display(123)


