# """
# Module utils: Provides utility functions for executing shell commands, file operations,
# environment variable management, and tool execution within agent algorithms.
# """

# from __future__ import annotations
# import os
# import subprocess
# import traceback
# import uuid
# from typing import TypeVar, Callable, Iterator, Any, Optional
# from pydantic import BaseModel, Field
# import asyncio


# # --------------------------------------------------------------------------
# # MODELS
# # --------------------------------------------------------------------------

# class ToolInput(BaseModel):
#     id: str
#     command: str
#     args: dict[str, Any] = Field(default_factory=dict)

# class ToolOutput(BaseModel):
#     """Standard output format for all tools."""
#     id: str = ""
#     success: bool = True
#     result: Any = None
#     error: str = ""
#     output: str = ""
#     tool_call_id: str | None = None

#     def get_output(self) -> str:
#         """Return a string for LLM consumption."""
#         if not self.success:
#             return self.error or "Unknown error"
#         return str(object=self.result if self.result is not None else self.output)


# # --------------------------------------------------------------------------
# # COMMAND / FILE MODELS + HELPERS
# # --------------------------------------------------------------------------

# class RunCommandInput(BaseModel):
#     """Input model for running a shell command."""
#     command: str = Field(default=..., description="Shell command to run.")
#     timeout: int = Field(default=300, description="Timeout in seconds.")
#     cwd: Optional[str] = Field(default=None, description="Current working directory for the command.")

# class RunCommandOutput(BaseModel):
#     """Output model for the result of running a shell command."""
#     stdout: str
#     stderr: str
#     returncode: int
#     command: str
#     cwd: str
#     env: dict[str, str]
#     execution_id: str
#     error: str | None = None
#     traceback_str: str | None = None

# class FileOpInput(BaseModel):
#     """Input model for file operations."""
#     filepath: str

# class FileContentOutput(BaseModel):
#     """Output model for file content operations."""
#     success: bool
#     error: str | None = None
#     traceback_str: str | None = None
#     content: str | None = None
#     files: list[str] | None = None

# class WriteFileInput(BaseModel):
#     """Input model for writing to a file."""
#     filepath: str
#     content: str
#     overwrite: bool = True

# class FileOpResult(BaseModel):
#     success: bool
#     error: str | None = None
#     content: str | None = None
#     files: list[str] | None = None

# class ReadLogInput(BaseModel):
#     """Input model for reading VSCode terminal output.
#     By default, this will read from the current VSCode terminal's output - no path needed.
#     You can optionally:
#     - Get the last N lines using num_lines
#     - Search for specific text using search_term
#     - Read from a different log file by specifying log_path
#     """
#     log_path: str | None = Field(default=None, description="Optional: Path to a specific log file. If not provided, reads from current VSCode terminal output")
#     num_lines: int | None = Field(default=None, description="Optional: Return only the last N lines")
#     search_term: str | None = Field(default=None, description="Optional: Return only lines containing this text")

# def _run_subprocess(command: str, timeout: int = 600) -> RunCommandOutput:
#     """Executes a subprocess with the specified command and timeout.
#     # Arguments
#         command: str
#             The command to run in the subprocess.
#         timeout: int
#             The maximum time to wait for the subprocess to complete.
#     # Returns
#         RunCommandOutput
#     """
#     execution_id = str(object=uuid.uuid4())
#     debug_env = dict(os.environ)
#     cwd = os.getcwd()
#     try:
#         args: list[str] = command.split()
#         result: subprocess.CompletedProcess[str] = subprocess.run(
#             args=args, capture_output=True, text=True, timeout=timeout
#         )
#         return RunCommandOutput(
#             stdout=result.stdout,
#             stderr=result.stderr,
#             returncode=result.returncode,
#             command=command,
#             cwd=cwd,
#             env=debug_env,
#             execution_id=execution_id,
#         )
#     except subprocess.TimeoutExpired as e:
#         return RunCommandOutput(
#             stdout="",
#             stderr=f"Timeout after {timeout} seconds",
#             returncode=-1,
#             command=command,
#             cwd=cwd,
#             env=debug_env,
#             execution_id=execution_id,
#             error=str(object=e),
#             traceback_str=traceback.format_exc(),
#         )
#     except Exception as e:
#         return RunCommandOutput(
#             stdout="",
#             stderr="",
#             returncode=-1,
#             command=command,
#             cwd=cwd,
#             env=debug_env,
#             execution_id=execution_id,
#             error=str(object=e),
#             traceback_str=traceback.format_exc(),
#         )

# # --------------------------------------------------------------------------
# # TOOL IMPLEMENTATIONS
# # --------------------------------------------------------------------------

# def do_run_command(input: RunCommandInput) -> RunCommandOutput:
#     """Run a terminal command in azure linux enviroment
#     # Arguments
#         input: RunCommandInput
#             The input model for running a command.
#     # Returns
#         RunCommandOutput
#     """
#     return _run_subprocess(command=input.command, timeout=input.timeout)

# def do_read_file(input: FileOpInput) -> FileContentOutput:
#     """
#     Reads the content of a file.
#     # Arguments
#         input: FileOpInput
#             The input model for reading a file.
#     # Returns
#         FileContentOutput
#     """
#     if not os.path.exists(path=input.filepath):
#         return FileContentOutput(success=False, error=f"File not found: {input.filepath}")
#     try:
#         with open(input.filepath, 'r', encoding='utf-8') as f:
#             content: str = f.read()
#         return FileContentOutput(success=True, content=content)
#     except Exception as e:
#         return FileContentOutput(
#             success=False, error=str(object=e), traceback_str=traceback.format_exc()
#         )

# def do_write_file(input: WriteFileInput) -> FileContentOutput:
#     """
#     Writes content to a file.
#     # Arguments
#         input: WriteFileInput
#             The input model for writing to a file.
#     # Returns
#         FileContentOutput
#     """
#     mode = 'w' if input.overwrite else 'a'
#     try:
#         with open(input.filepath, mode, encoding='utf-8') as f:
#             f.write(input.content)
#         return FileContentOutput(success=True)
#     except Exception as e:
#         return FileContentOutput(
#             success=False, error=str(object=e), traceback_str=traceback.format_exc()
#         )

# def do_delete_file(input: FileOpInput) -> FileContentOutput:
#     """
#     Deletes a file.
#     # Arguments
#         input: FileOpInput
#             The input model for deleting a file.
#     # Returns
#         FileContentOutput
#     """
#     if not os.path.exists(path=input.filepath):
#         return FileContentOutput(success=False, error=f"File not found: {input.filepath}")
#     try:
#         os.remove(path=input.filepath)
#         return FileContentOutput(success=True)
#     except Exception as e:
#         return FileContentOutput(
#             success=False, error=str(object=e), traceback_str=traceback.format_exc()
#         )

# def do_list_files(directory: str = '.') -> FileContentOutput:
#     """
#     Lists all files in a directory.
#     # Arguments
#         directory: str
#             The directory to list files in.
#     # Returns
#         FileContentOutput
#     """
#     try:
#         files: list[str] = [
#             f for f in os.listdir(path=directory)
#             if os.path.isfile(path=os.path.join(directory, f))
#         ]
#         return FileContentOutput(success=True, files=files)
#     except Exception as e:
#         return FileContentOutput(
#             success=False, error=str(object=e), traceback_str=traceback.format_exc()
#         )

# def do_install_package(package_name: str) -> FileContentOutput:
#     """
#     Installs a Python package using pip.
#     # Arguments
#         package_name: str
#             The name of the package to install.
#     # Returns
#         FileContentOutput
#     """
#     cmd: str = f'pip install {package_name}'
#     result: RunCommandOutput = _run_subprocess(command=cmd, timeout=600)
#     if result.returncode == 0:
#         return FileContentOutput(
#             success=True, content=f"Installed {package_name} successfully."
#         )
#     return FileContentOutput(
#         success=False,
#         error=f"Failed to install {package_name}. Stderr: {result.stderr}",
#         traceback_str=result.traceback_str,
#     )

# def do_run_tests(test_command: str = "pytest --maxfail=1 --disable-warnings -q") -> RunCommandOutput:
#     """
#     Run tests using pytest.
#     # Arguments
#         test_command: str
#             The command to run tests.
#     # Returns
#         RunCommandOutput
#     """
#     return _run_subprocess(command=test_command, timeout=300)

# def do_lint_code(lint_command: str = "flake8 .") -> RunCommandOutput:
#     """
#     Lint code using flake8.
#     # Arguments
#         lint_command: str
#             The command to lint code.
#     # Returns
#         RunCommandOutput
#     """
#     return _run_subprocess(command=lint_command, timeout=300)

# def do_search_docs(query: str) -> FileContentOutput:
#     """
#     Search documentation for a query.
#     # Arguments
#         query: str
#             The query to search for in the documentation.
#     # Returns
#         FileContentOutput
#     """
#     return FileContentOutput(
#         success=True,
#         content=f"Docs search results for '{query}' not implemented."
#     )

# def get_env_var(var_name: str) -> FileContentOutput:
#     """
#     Get the value of an environment variable.
#     # Arguments
#         var_name: str
#             The name of the environment variable.
#     # Returns
#         FileContentOutput
#     """
#     val: str = os.environ.get(var_name, default='')
#     return FileContentOutput(success=True, content=val)

# def set_env_var(var_name: str, value: str) -> FileContentOutput:
#     """
#     Set the value of an environment variable.
#     # Arguments
#         var_name: str
#             The name of the environment variable.
#         value: str
#             The value to set the environment variable to.
#     # Returns
#         FileContentOutput
#     """
#     try:
#         os.environ[var_name] = value
#         return FileContentOutput(success=True)
#     except Exception as e:
#         return FileContentOutput(
#             success=False, error=str(object=e), traceback_str=traceback.format_exc()
#         )

# def recursive_search_file(directory: str, filename: str) -> str | None:
#     """
#     Recursively search for a file in a directory.
#     # Arguments
#         directory: str
#             The directory to search in.
#         filename: str
#             The name of the file to search for.
#     # Returns
#         str | None
#             The path to the file if found, else None.
#     """
#     for root, _, files in os.walk(top=directory):
#         if filename in files:
#             return os.path.join(root, filename)
#     return None

# def read_file_lines(filepath: str) -> Iterator[str]:
#     """
#     Read lines from a file.
#     # Arguments
#         filepath: str
#             The path to the file to read.
#     # Returns
#         Iterator[str]
#             An iterator over the lines of the file.
#     """
#     try:
#         with open(file=filepath, mode='r', encoding='utf-8') as file:
#             for line in file:
#                 yield line
#     except Exception as e:
#         yield f"Error reading file: {str(object=e)}"

# def recursive_list_files(directory: str) -> list[str]:
#     """
#     Recursively list all files in a directory.
#     # Arguments
#         directory: str
#             The directory to list files in.
#     # Returns
#         list[str]
#             A list of all files in the directory.
#     """
#     files_list = []
#     for root, _, files in os.walk(directory):
#         for file in files:
#             files_list.append(os.path.join(root, file))
#     return files_list

# def recursive_search_keyword(directory: str, keyword: str) -> list[str]:
#     """
#     Recursively search for a keyword in files in a directory.
#     # Arguments
#         directory: str
#             The directory to search in.
#         keyword: str
#             The keyword to search for.
#     # Returns
#         list[str]
#             A list of file paths containing the keyword.
#     """
#     matches = []
#     for root, _, files in os.walk(directory):
#         for file in files:
#             filepath: str = os.path.join(root, file)
#             try:
#                 with open(file=filepath, mode='r', encoding='utf-8') as f:
#                     if keyword in f.read():
#                         matches.append(filepath)
#             except:
#                 continue
#     return matches

# def get_powershell_output() -> str:
#     """Get the PowerShell terminal output using PowerShell's PSReadLine history."""
#     try:
#         # Get the default PowerShell history file path
#         history_path = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt")
        
#         if os.path.exists(history_path):
#             with open(history_path, 'r', encoding='utf-8') as f:
#                 content = f.read()
#             return content
        
#         # Fallback: try to get history through command
#         result = _run_subprocess('powershell -Command "Get-History | Format-List CommandLine"')
#         if result.returncode == 0 and result.stdout:
#             return result.stdout
            
#         return ""
#     except Exception:
#         return ""

# def read_logs(input: ReadLogInput) -> FileContentOutput:
#     """Read the terminal output or a specific log file.
#     By default (with no parameters), this reads the current terminal output.
#     No path specification is needed for reading the current terminal.
    
#     Examples:
#         read_logs(ReadLogInput())  # Read all current terminal output
#         read_logs(ReadLogInput(num_lines=100))  # Read last 100 lines of terminal
#         read_logs(ReadLogInput(search_term="error"))  # Find all terminal lines containing "error"
#     """
#     try:
#         # If a specific log path is provided, use that
#         if input.log_path:
#             if not os.path.exists(path=input.log_path):
#                 return FileContentOutput(success=False, error=f"Log file not found: {input.log_path}")
#             with open(input.log_path, 'r', encoding='utf-8') as f:
#                 content = f.read()
#         else:
#             # Get PowerShell output directly
#             content = get_powershell_output()
#             if not content:
#                 return FileContentOutput(success=False, error="Could not retrieve PowerShell output")

#         # Process the content based on search_term or num_lines
#         lines = content.splitlines()
        
#         if input.search_term:
#             matching_lines = [line for line in lines if input.search_term in line]
#             return FileContentOutput(success=True, content="\n".join(matching_lines))
        
#         if input.num_lines:
#             last_n = lines[-input.num_lines:]
#             return FileContentOutput(success=True, content="\n".join(last_n))
        
#         return FileContentOutput(success=True, content=content)
            
#     except Exception as e:
#         return FileContentOutput(
#             success=False,
#             error=str(object=e),
#             traceback_str=traceback.format_exc()
#         )

# # --------------------------------------------------------------------------
# # TOOL REGISTRY + EXECUTOR
# # --------------------------------------------------------------------------

# T = TypeVar('T')
# ToolResult = FileContentOutput | RunCommandOutput | list[str]
# ToolInputType = FileOpInput | RunCommandInput | WriteFileInput | None

# # The fourth item in each tuple is "is_async" -> for truly async fns. (All here are sync.)
# TOOL_REGISTRY: dict[str, tuple[Callable, type[BaseModel] | None, list[str], bool]] = {
#     "do_read_file": (do_read_file, FileOpInput, ["filepath"], False),
#     "do_write_file": (do_write_file, WriteFileInput, ["filepath", "content", "overwrite"], False),
#     "do_delete_file": (do_delete_file, FileOpInput, ["filepath"], False),
#     "do_list_files": (do_list_files, None, ["directory"], False),
#     "do_run_command": (do_run_command, RunCommandInput, ["command", "timeout"], False),
#     "do_lint_code": (do_lint_code, None, ["lint_command"], False),
#     "do_run_tests": (do_run_tests, None, ["test_command"], False),
#     "do_install_package": (do_install_package, None, ["package_name"], False),
#     "recursive_search_keyword": (recursive_search_keyword, None, ["directory", "keyword"], False),
#     "read_logs": (read_logs, ReadLogInput, ["log_path", "num_lines", "search_term"], False),
# }

# async def execute_tool(tool_name: str, tool_call_id: str | None = None, **kwargs) -> ToolOutput:
#     """
#     Execute a tool and return standardized output.
#     The tool may be sync or async (is_async).
#     # Arguments
#         tool_name: str
#             The name of the tool to execute.
#         tool_call_id: str | None
#             Optional ID to map tool calls to their responses.
#         **kwargs: dict
#             The arguments to pass to the tool.
#     # Returns
#         ToolOutput
#     """
#     if tool_name not in TOOL_REGISTRY:
#         return ToolOutput(success=False, error=f"Unknown tool: {tool_name}", tool_call_id=tool_call_id)

#     func, input_model, params, is_async = TOOL_REGISTRY[tool_name]

#     # Validate required arguments
#     for param in params:
#         if param not in kwargs:
#             raise ValueError(f"Missing required argument '{param}' for tool '{tool_name}'")

#     try:
#         if input_model:
#             input_args = {k: kwargs[k] for k in params}
#             input_instance = input_model(**input_args)
#         else:
#             input_instance = None

#         # If the function is truly async
#         if is_async:
#             if input_instance:
#                 raw_result = await func(input_instance)  # type: ignore
#             else:
#                 raw_result = await func(**kwargs)        # type: ignore
#         else:
#             # Synchronous => run in a thread
#             if input_instance:
#                 raw_result = await asyncio.to_thread(func, input_instance)
#             else:
#                 raw_result = await asyncio.to_thread(func, **kwargs)

#         # Convert raw_result to ToolOutput if needed
#         if isinstance(raw_result, ToolOutput):
#             raw_result.tool_call_id = tool_call_id
#             return raw_result

#         if hasattr(raw_result, "success"):
#             # e.g. FileContentOutput or RunCommandOutput
#             success = getattr(raw_result, "success", True)
#             error = getattr(raw_result, "error", "")
#             content = getattr(raw_result, "content", None)
#             stdout = getattr(raw_result, "stdout", "")
#             files_ = getattr(raw_result, "files", None)

#             # Combine into a single string if needed
#             out_str = stdout or (str(files_) if files_ else "")
#             return ToolOutput(
#                 success=success,
#                 error=error,
#                 result=content,
#                 output=out_str,
#                 tool_call_id=tool_call_id
#             )

#         if isinstance(raw_result, list):
#             # e.g. a list of files from recursive_search_keyword
#             return ToolOutput(success=True, result=raw_result, tool_call_id=tool_call_id)

#         # Fallback: if raw_result is any other object/string
#         return ToolOutput(success=True, result=raw_result, tool_call_id=tool_call_id)

#     except Exception as e:
#         return ToolOutput(
#             success=False,
#             error=f"Tool execution failed: {e}\n{traceback.format_exc()}",
#             tool_call_id=tool_call_id
#         )

# # async def explain_tools(context: RunContext[dict]):
# #     """
# #     Summarize each tool's purpose to the user (for debugging/troubleshooting).
# #     """
# #     tools_info = [
# #         ("read_logs", read_logs.__doc__),
# #         ("do_run_command", do_run_command.__doc__),
# #         ("do_list_files", do_list_files.__doc__),
# #         ("do_read_file", do_read_file.__doc__),
# #         ("do_lint_code", do_lint_code.__doc__),
# #         ("do_run_tests", do_run_tests.__doc__),
# #         ("do_delete_file", do_delete_file.__doc__),
# #         ("recursive_search_file", recursive_search_file.__doc__),
# #         ("recursive_search_keyword", recursive_search_keyword.__doc__),
# #         ("message_user", message_user.__doc__),
# #         ("think_and_plan", think_and_plan.__doc__),
# #         ("explain_tools", explain_tools.__doc__),
# #     ]
# #     summary = "\n".join(
# #         f"**{name}**:\n{doc if doc else '(no docstring)'}\n"
# #         for (name, doc) in tools_info
# #     )
# #     console.print(Panel(summary, title="Tool Explanations", border_style="yellow"))
# #     return context.deps