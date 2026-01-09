"""Prompt Builder - System Prompt Management"""
from typing import Iterable


def build_system_prompt(available_tools: Iterable[str]) -> str:
    """
    Build system prompt for the agent
    
    Args:
        available_tools: List of available tool names
        
    Returns:
        Formatted system prompt
    """
    tools_list = "\n".join([f"- {tool}" for tool in available_tools])
    
    prompt = f"""You are a helpful AI agent with access to the following tools:

{tools_list}

Your task is to:
1. Understand the user's request
2. Determine which tools (if any) are needed
3. Execute the appropriate tools
4. Provide a helpful response

When using tools:
- Choose the most appropriate tool for the task
- Execute tools with correct parameters
- Interpret tool results accurately
- Provide clear explanations to the user

Always be helpful, accurate, and concise in your responses.
"""
    
    return prompt


def build_tool_prompt(tool_name: str, tool_description: str, parameters: dict) -> str:
    """
    Build prompt for a specific tool
    
    Args:
        tool_name: Name of the tool
        tool_description: Description of what the tool does
        parameters: Expected parameters
        
    Returns:
        Formatted tool prompt
    """
    params = "\n".join([f"  - {k}: {v}" for k, v in parameters.items()])
    
    return f"""Tool: {tool_name}
Description: {tool_description}
Parameters:
{params}
"""
