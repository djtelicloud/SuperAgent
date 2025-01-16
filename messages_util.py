from rich.table import Table


def create_tool_result_table(tool_name: str, test_results: list[dict]) -> Table:
    """Create a rich table to display tool test results."""
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
    
    return table

def process_agent_messages(response):
    """
    Process agent messages and their parts, tracking and displaying tool results.
    
    Args:
        response: The response object containing messages to process
        
    Returns:
        dict: A dictionary containing tool results counts
    """
    tool_results = {}
    current_tool_calls = {}
    
    # Process all messages and their parts
    for msg in response._all_messages:
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if hasattr(part, 'part_kind'):
                    if part.part_kind == 'tool-call':
                        # Track tool call
                        tool_name = getattr(part, 'tool_name', 'unknown')
                        if tool_name not in tool_results:
                            tool_results[tool_name] = 0
                            current_tool_calls[tool_name] = []
                        
                        tool_results[tool_name] += 1
                        # Store input for this tool call
                        current_tool_calls[tool_name].append({
                            'input': getattr(part, 'args', ''),
                            'success': False
                        })
                        
                    elif part.part_kind == 'tool-return':
                        # Update the last result for this tool
                        tool_name = getattr(part, 'tool_name', 'unknown')
                        if tool_name in current_tool_calls and current_tool_calls[tool_name]:
                            current_tool_calls[tool_name][-1].update({
                                'output': getattr(part, 'content', ''),
                                'success': True
                            })
                            
                            # Create a clean table for the current tool call
                            table = Table(
                                title=f"Tool Call: {tool_name}",
                                show_header=True,
                                header_style="bold magenta",
                                border_style="blue"
                            )
                            table.add_column("Parameter", style="cyan")
                            table.add_column("Value", style="green")
                            
                            # Add input parameters
                            if hasattr(current_tool_calls[tool_name][-1]['input'], 'args_json'):
                                table.add_row("Input", str(current_tool_calls[tool_name][-1]['input'].args_json))
                            else:
                                table.add_row("Input", str(current_tool_calls[tool_name][-1]['input']))
                            
                            # Add output with proper formatting
                            output = current_tool_calls[tool_name][-1]['output']
                            if isinstance(output, dict):
                                for key, value in output.items():
                                    table.add_row(key, str(value))
                            else:
                                table.add_row("Output", str(output))
                            
                            # Add status
                            table.add_row(
                                "Status",
                                "[green]✓ Success[/green]" if current_tool_calls[tool_name][-1]['success'] else "[red]✗ Failed[/red]"
                            )
                            
                            print(table)
                            
                    elif part.part_kind == 'retry-prompt':
                        tool_results['retry_prompt'] = True
    # Convert current_tool_calls to a list of dictionaries
    test_results_list = [dict(tool_name=key, **value) for key, values in current_tool_calls.items() for value in values]
    table = create_tool_result_table(tool_name, test_results=test_results_list)
    print(table)
                        
    return tool_results 