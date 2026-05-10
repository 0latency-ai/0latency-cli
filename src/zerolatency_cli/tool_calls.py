"""Tool-call chain parsing and atomization."""

import re
from typing import List
from zerolatency_cli.atom import Atom


def parse_tool_calls(text: str) -> List[tuple[int, int, str]]:
    """
    Parse tool-call blocks from text.
    
    Detects <function_calls>...</function_calls> blocks and extracts individual
    <invoke> tool calls.
    
    Args:
        text: Text potentially containing tool calls
        
    Returns:
        List of (start_pos, end_pos, tool_call_content) tuples
    """
    tool_calls = []
    
    # Find <function_calls> blocks
    function_calls_pattern = re.compile(
        r'<function_calls>(.*?)</function_calls>',
        re.DOTALL | re.IGNORECASE
    )
    
    for fc_match in function_calls_pattern.finditer(text):
        fc_content = fc_match.group(1)
        
        # Find individual <invoke> blocks within function_calls
        invoke_pattern = re.compile(
            r'<invoke[^>]*>(.*?)</invoke>',
            re.DOTALL | re.IGNORECASE
        )
        
        for invoke_match in invoke_pattern.finditer(fc_content):
            # Get absolute position in original text
            start = fc_match.start() + invoke_match.start()
            end = fc_match.start() + invoke_match.end()
            content = invoke_match.group(0)  # Full <invoke>...</invoke> block
            tool_calls.append((start, end, content))
    
    return tool_calls


def atomize_tool_calls(atom: Atom) -> List[Atom]:
    """
    Split an atom containing tool calls into multiple atoms (one per tool call).
    
    Args:
        atom: Atom potentially containing tool-call blocks
        
    Returns:
        List of atoms (original if no tool calls, split if tool calls detected)
    """
    # Check if content contains tool calls
    tool_calls = parse_tool_calls(atom.content)
    
    if not tool_calls:
        # No tool calls, return original atom
        return [atom]
    
    if len(tool_calls) == 1:
        # Single tool call, just add metadata to original atom
        atom.tool_call_index = None  # Not a chain
        atom.tool_call_total = None
        return [atom]
    
    # Multiple tool calls - create atom for each
    atomized = []
    for i, (start, end, content) in enumerate(tool_calls):
        # Create new atom with same base metadata
        tool_atom = Atom(
            role=atom.role,
            content=content,
            content_raw=content.encode('utf-8'),
            timestamp=atom.timestamp,
            agent_id=atom.agent_id,
            agent_name=atom.agent_name,
            agent_version=atom.agent_version,
            verbatim=atom.verbatim,
            surface=atom.surface,
            tool_payload=content,  # Store tool call as payload
            tenant_id=atom.tenant_id,
            tool_call_index=i,
            tool_call_total=len(tool_calls),
        )
        atomized.append(tool_atom)
    
    return atomized
