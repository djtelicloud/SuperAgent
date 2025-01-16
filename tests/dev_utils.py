# from datetime import datetime
# import os
# import sys
# import traceback
# from main_utils import ToolInput, ToolOutput
# from logging_utils import EnterpriseLogger
# import sys
# from datetime import datetime, UTC

# from agent_prompts import prompts
# from pydantic_ai import RunContext, Agent
# from agent_prompts import prompts
# import os
# from display_utils import CustomPrint
# from azure_agent import openai_model
# from agent_prompts import prompts
# import platform
# import subprocess


# SYSTEM_PROMPT = prompts["SYSTEM_PROMPT"]

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

# customPrint = CustomPrint()


# class PydanticUtils:
#     """
#     A utility class providing environment detection, error tracking,
#     and debugging capabilities for Azure-related operations.

#     The class offers environment detection, error analysis, and debugging tools
#     with a single main entrypoint: run_tool(), which takes a ToolInput and returns
#     a ToolOutput containing environment information and any error analysis.

#     Args:
#         logit (EnterpriseLogger): The logger instance for tracking errors and messages.

#     Methods:
#         run_tool(tool_input: ToolInput) -> ToolOutput: Main entrypoint that runs environment detection and checks.
#         detect_environment() -> ToolOutput: Detects the current environment configuration.
#         check_environment() -> ToolOutput: Compiles a summary of the environment context.
#         analyze_error(error_str: str, context_str: str) -> ToolOutput: Suggests fixes for known error patterns.
#         debug_error(error: str, context_str: str = "") -> ToolOutput: Logs errors and provides debugging information.

#     Usage:
#         logger = EnterpriseLogger("example@email.com")
#         utils = PydanticUtils(logger)
#         result = utils.run_tool(tool_input)
#         # Or use individual methods:
#         env_info = utils.check_environment()
#         debug_info = utils.debug_error(error, "context")
#     """

#     def __init__(self, logit: EnterpriseLogger):
#         self.logit = logit
#         self.id = logit.session_id
#         self.error_history: list = []
#         self.env_context: dict = {}
#         self.working_dir: str = os.getcwd()
#         self.debug_context: dict = {
#             "error_count": 0,
#             "last_error": None,
#             "error_history": [],
#             "active_fixes": [],
#             "environment": ""
#         }


#     @agent.tool_plain
#     def detect_environment(self) -> ToolOutput:
#         """
#         Detects the environment configuration.
#         """
#         env_context = {
#             "type": "local",
#             "python_version": f"Python {sys.version_info.major}.{sys.version_info.minor}",
#             "compute_target": None,
#             "workspace_name": None,
#             "subscription_id": None,
#             "resource_group": None,
#             "is_interactive": True
#         }
#         try:
#             if "AZUREML_RUN_ID" in os.environ:
#                 env_context.update({
#                     "type": "azureml",
#                     "compute_target": os.environ.get("AZUREML_COMPUTE_NAME", ""),
#                     "workspace_name": os.environ.get("AZUREML_WORKSPACE_NAME", ""),
#                     "subscription_id": os.environ.get("AZUREML_SUBSCRIPTION_ID", ""),
#                     "resource_group": os.environ.get("AZUREML_RESOURCE_GROUP", ""),
#                     "is_interactive": "ipykernel" in sys.modules
#                 })
#             elif os.environ.get("AZURE_HTTP_USER_AGENT", "").startswith("cloud-shell"):
#                 env_context["type"] = "azure_cloud_shell"
#             self.env_context = env_context
#             self.debug_context["environment"] = env_context.get("type", "")
#             return ToolOutput(
#                 id="detect_environment",
#                 tool_call_id=None,
#                 success=True,
#                 result=env_context,
#                 error="",
#                 output=""
#             )
#         except Exception as e:
#             self.logit.log_error(e)
#             self.logit.log_message("Error detecting environment, defaulting to local")
#             return ToolOutput(
#                 id="detect_environment",
#                 tool_call_id=None,
#                 success=False,
#                 result=None,
#                 error=str(e),
#                 output=""
#             )

#     @agent.tool_plain
#     def check_environment(self) -> ToolOutput:
#         """
#         Compiles a summary of the environment context and returns it.
#         """
#         try:
#             env_vars = {
#                 "Azure ML Variables": [v for v in os.environ.keys() if v.startswith("AZUREML_")],
#                 "Azure Variables": [v for v in os.environ.keys() if v.startswith("AZURE_")],
#                 "OpenAI Variables": [v for v in os.environ.keys() if v.startswith("OPENAI_")]
#             }
            
#             checks = {
#                 "Environment": {
#                     "Type": self.env_context.get("type", "N/A"),
#                     "Python Version": self.env_context.get("python_version", "N/A"),
#                     "Current Directory": os.getcwd()
#                 },
#                 "Azure ML Config": {
#                     "Workspace": self.env_context.get("workspace_name", "N/A"),
#                     "Compute Target": self.env_context.get("compute_target", "N/A"),
#                     "Interactive": str(self.env_context.get("is_interactive", "N/A"))
#                 },
#                 "Environment Variables": env_vars
#             }
            
#             try:
#                 customPrint.create_status_table(checks)
#                 formatted_output = customPrint.get_formatted_output()
#             except AssertionError as console_err:
#                 self.logit.log_message(f"Console output error: {str(console_err)}", level="warning")
#                 formatted_output = str(checks)  # Fallback to raw dict string if console formatting fails
            
#             return ToolOutput(
#                 id="check_environment",
#                 tool_call_id=None,
#                 success=True,
#                 result=checks,
#                 error="",
#                 output=formatted_output
#             )
#         except Exception as e:
#             self.logit.log_error(e)
#             return ToolOutput(
#                 id="check_environment",
#                 tool_call_id=None,
#                 success=False,
#                 result=None,
#                 error=str(e),
#                 output=""
#             )

#     @agent.tool_plain
#     def analyze_error(self, error_str: str, context_str: str) -> ToolOutput:
#         """
#         Examines the error to suggest potential fixes based on known patterns.
#         """
#         fixes = []
#         err_str = error_str.lower()
#         ctx_str = context_str.lower()

#         # Authentication errors
#         if "authentication failed" in err_str or "unauthorized" in err_str:
#             fixes.extend([
#                 "Check Azure credentials in environment variables",
#                 "Run 'az login' to refresh Azure CLI session",
#                 "Verify service principal permissions",
#                 "Check managed identity configuration"
#             ])
        
#         # Module/Import errors
#         elif "modulenotfounderror" in err_str or "no module named" in err_str:
#             module = err_str.split("'")[1] if "'" in err_str else "the required module"
#             fixes.extend([
#                 f"Install {module} using pip: pip install {module}",
#                 "Check Python environment and activation",
#                 "Verify package is listed in requirements.txt"
#             ])
        
#         # Connection errors
#         elif "connection" in err_str or "timeout" in err_str:
#             fixes.extend([
#                 "Check network connectivity",
#                 "Verify Azure endpoints accessibility",
#                 "Check firewall rules and NSG configuration",
#                 "Verify proxy settings if applicable"
#             ])

#         # Azure-specific context
#         if "azure" in ctx_str:
#             fixes.extend([
#                 "Verify Azure subscription is active",
#                 "Check resource provider registration",
#                 "Verify resource group exists",
#                 "Check Azure region availability"
#             ])

#         # If no specific fixes found, add general debugging steps
#         if not fixes:
#             fixes.extend([
#                 "Check system requirements",
#                 "Verify environment variables",
#                 "Review documentation",
#                 "Check logs for detailed error messages"
#             ])

#         return ToolOutput(
#             id="analyze_error",
#             tool_call_id=None,
#             success=True,
#             result=fixes,
#             error="",
#             output=str(fixes)
#         )

#     @agent.tool_plain
#     def debug_error(self, error: str, context_str: str = "") -> ToolOutput:
#         """
#         Logs the error and attaches any suggested fixes, returning all info in a ToolOutput.
#         """
#         try:
#             self.debug_context["error_count"] += 1
#             self.debug_context["last_error"] = error
#             error_entry = {
#                 "timestamp": datetime.now(UTC).isoformat(),
#                 "error": error,
#                 "type": "error",
#                 "context": context_str,
#                 "traceback": traceback.format_exc()
#             }
#             self.debug_context["error_history"].append(error_entry)

#             # Analyze the error to get recommended fixes
#             fix_res = self.analyze_error(error, context_str)
#             if fix_res.success and fix_res.result:
#                 fixes = fix_res.result
#             else:
#                 fixes = []

#             self.debug_context["active_fixes"].extend(fixes)

#             debug_response = (
#                 "## Error Analysis\n"
#                 f"**Error:** {error}\n"
#                 f"**Context:** {context_str}\n\n"
#                 "### Suggested Fixes:\n"
#                 + "\n".join(f"- {fix}" for fix in fixes)
#                 + "\n\n"
#                 f"### Environment Check:\n"
#                 f"- Running in: {self.debug_context['environment']}\n"
#                 f"- Error count: {self.debug_context['error_count']}\n"
#                 f"- Active fixes: {self.debug_context['active_fixes']}\n\n"
#                 "### Next Steps:\n"
#                 "1. Review suggested fixes\n"
#                 "2. Apply any relevant solutions\n"
#                 "3. Verify environment configuration\n"
#                 "4. Review error history for patterns\n"
#             )
#             customPrint.display_message(debug_response, style="error")
#             return ToolOutput(
#                 id="debug_error",
#                 tool_call_id=None,
#                 success=True,
#                 result=error_entry,
#                 error="",
#                 output=customPrint.get_formatted_output()
#             )
#         except Exception as e2:
#             self.logit.log_error(e2)
#             return ToolOutput(
#                 id="debug_error",
#                 tool_call_id=None,
#                 success=False,
#                 result=None,
#                 error=str(e2),
#                 output=""
#             )


#     @agent.tool_plain
#     def run_tool(self, tool_input: ToolInput) -> ToolOutput:
#         """
#         Single entrypoint for this utility. It will:
#         1) Detect the environment,
#         2) Check the environment, 
#         3) Compile a final report,
#         4) If any errors occur, they are added to the final output.
#         """
#         try:
#             # 1) Detect Environment
#             env_res: ToolOutput = self.detect_environment()
#             if not env_res.success:
#                 return env_res

#             # 2) Check Environment
#             check_res: ToolOutput = self.check_environment()
#             if not check_res.success:
#                 return check_res

#             # 3) Compile results
#             results = {
#                 "Environment Status": check_res.result,
#                 "Debug Info": {
#                     "Error Count": self.debug_context["error_count"],
#                     "Last Error": self.debug_context["last_error"],
#                     "Active Fixes": self.debug_context["active_fixes"]
#                 }
#             }
            
#             try:
#                 customPrint.create_status_table(results)
#                 formatted_output = customPrint.get_formatted_output()
#             except AssertionError as console_err:
#                 self.logit.log_message(f"Console output error: {str(console_err)}", level="warning")
#                 formatted_output = str(results)
            
#             return ToolOutput(
#                 id=tool_input.id,
#                 tool_call_id=None,
#                 success=True,
#                 result=results,
#                 error="",
#                 output=formatted_output
#             )
#         except Exception as e:
#             debug_res = self.debug_error(str(e), "run_tool")
#             return ToolOutput(
#                 id=tool_input.id,
#                 tool_call_id=None,
#                 success=False,
#                 result=None,
#                 error=str(e),
#                 output=debug_res.output if debug_res.output else ""
#             )


# if __name__ == "__main__":
#     logger = EnterpriseLogger(user_email="djtelicloud@gmail.com")
#     p_utils = PydanticUtils(logit=logger)
#     test_windows_cmd = "dir"
#     result = p_utils.run_tool(tool_input=ToolInput(id="test_run", command=test_windows_cmd, args={}))
#     #display result
#     customPrint.display_message(result.output, style="info")




