# import unittest
# from display_utils import CustomPrint
# from dev_utils import PydanticUtils
# from main_utils import ToolInput, ToolOutput
# from logging_utils import EnterpriseLogger
# import os

# class TestCustomPrint(unittest.TestCase):
#     def setUp(self):
#         self.printer = CustomPrint()
        
#     def tearDown(self):
#         """Clear console output after each test"""
#         self.printer.clear_output()
        
#     def test_display_message_plain(self):
#         """Test plain text display"""
#         self.printer.display_message("Hello World")
#         output = self.printer.get_formatted_output()
#         self.assertIn("Hello World", output)
        
#     def test_display_message_markdown(self):
#         """Test markdown text display"""
#         self.printer.display_message("## Hello\n**World**")
#         output = self.printer.get_formatted_output()
#         self.assertIn("Hello", output)
#         self.assertIn("World", output)
        
#     def test_display_message_code(self):
#         """Test code display"""
#         self.printer.display_message("def hello():\n    print('world')")
#         output = self.printer.get_formatted_output()
#         self.assertIn("hello", output)
#         self.assertIn("print", output)
        
#     def test_display_dict(self):
#         """Test dictionary display"""
#         test_dict = {"key1": "value1", "key2": "value2"}
#         self.printer.display(test_dict)
#         output = self.printer.get_formatted_output()
#         self.assertIn("key1", output)
#         self.assertIn("value1", output)
        
#     def test_create_status_table(self):
#         """Test table creation"""
#         test_data = {
#             "Environment": {"Type": "local", "Python": "3.8"},
#             "Status": "Active"
#         }
#         self.printer.create_status_table(test_data)
#         output = self.printer.get_formatted_output()
#         self.assertIn("Environment", output)
#         self.assertIn("Status", output)
        
#     def test_display_code_diff(self):
#         """Test code diff display"""
#         original = "print('hello')"
#         modified = "print('world')"
#         self.printer.display_code_diff(original, modified)
#         output = self.printer.get_formatted_output()
#         self.assertIn("hello", output)
#         self.assertIn("world", output)

# class TestPydanticUtils(unittest.TestCase):
#     def setUp(self):
#         self.logger = EnterpriseLogger(user_email="test@example.com")
#         self.utils = PydanticUtils(logit=self.logger)
        
#     def test_detect_environment(self):
#         """Test environment detection"""
#         result = self.utils.detect_environment()
#         self.assertTrue(result.success)
#         self.assertIsNotNone(result.result)
        
#     def test_check_environment(self):
#         """Test environment check"""
#         result = self.utils.check_environment()
#         self.assertTrue(result.success)
#         self.assertIsNotNone(result.result)
        
#     def test_analyze_error(self):
#         """Test error analysis"""
#         result = self.utils.analyze_error(
#             "authentication failed", 
#             "trying to access Azure resources"
#         )
#         self.assertTrue(result.success)
#         self.assertIsNotNone(result.result)
        
#     def test_debug_error(self):
#         """Test error debugging"""
#         result = self.utils.debug_error(
#             "Test error",
#             "Test context"
#         )
#         self.assertTrue(result.success)
#         self.assertIsNotNone(result.result)

#     def test_run_tool_success(self):
#         """Test successful tool run"""
#         tool_input = ToolInput(
#             id="test_run",
#             command="dir" if os.name == 'nt' else "ls",
#             args={}
#         )
#         result = self.utils.run_tool(tool_input)
#         self.assertTrue(result.success)
        
#     def test_run_tool_failure(self):
#         """Test failed tool run"""
#         tool_input = ToolInput(
#             id="test_run",
#             command="nonexistent_command_xyz",
#             args={}
#         )
#         result = self.utils.run_tool(tool_input)
#         self.assertFalse(result.success)
#         self.assertIsNotNone(result.error)
#         self.assertIn("nonexistent", str(result.error).lower())

# class TestLLMInteractions(unittest.TestCase):
#     def setUp(self):
#         self.logger = EnterpriseLogger(user_email="test@example.com")
#         self.utils = PydanticUtils(logit=self.logger)
        
#     def test_llm_error_analysis(self):
#         """Test LLM-based error analysis"""
#         error = "ModuleNotFoundError: No module named 'azure.core'"
#         context = "Attempting to use Azure SDK"
#         result = self.utils.analyze_error(error, context)
#         self.assertTrue(result.success)
#         self.assertIn("azure", str(result.result).lower())
        
#     def test_llm_debug_suggestions(self):
#         """Test LLM-based debugging suggestions"""
#         error = "ConnectionError: Failed to establish connection"
#         result = self.utils.debug_error(error, "Azure API call")
#         self.assertTrue(result.success)
#         self.assertIsNotNone(result.result)

# if __name__ == '__main__':
#     unittest.main(verbosity=2) 