"""Tests for tool-call chain atomization."""

import pytest
from zerolatency_cli.atom import Atom
from zerolatency_cli.tool_calls import parse_tool_calls, atomize_tool_calls


def test_no_tool_calls():
    """Test that regular text is not atomized."""
    atom = Atom(
        role="assistant",
        content="Just regular text response",
        content_raw=b"Just regular text response",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    atomized = atomize_tool_calls(atom)
    
    assert len(atomized) == 1
    assert atomized[0] is atom  # Same object


def test_single_tool_call():
    """Test that single tool call is not split (not a chain)."""
    content = """Here's the result:
<function_calls>
<invoke name="read_file">
<parameter name="path">test.txt</parameter>
</invoke>
</function_calls>
"""
    
    atom = Atom(
        role="assistant",
        content=content,
        content_raw=content.encode('utf-8'),
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    atomized = atomize_tool_calls(atom)
    
    # Single tool call - not considered a chain
    assert len(atomized) == 1
    assert atomized[0].tool_call_index is None
    assert atomized[0].tool_call_total is None


def test_multi_tool_call_chain():
    """Test that multi-tool-call blocks are split into separate atoms."""
    content = """I'll call three tools:
<function_calls>
<invoke name="read_file">
<parameter name="path">file1.txt</parameter>
</invoke>
<invoke name="read_file">
<parameter name="path">file2.txt</parameter>
</invoke>
<invoke name="write_file">
<parameter name="path">output.txt</parameter>
</invoke>
</function_calls>
"""
    
    atom = Atom(
        role="assistant",
        content=content,
        content_raw=content.encode('utf-8'),
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    atomized = atomize_tool_calls(atom)
    
    # Should have 3 atoms (one per tool call)
    assert len(atomized) == 3
    
    # Check metadata
    for i, tool_atom in enumerate(atomized):
        assert tool_atom.tool_call_index == i
        assert tool_atom.tool_call_total == 3
        assert "<invoke" in tool_atom.content
    
    # First should be read_file for file1.txt
    assert "file1.txt" in atomized[0].content
    # Second should be read_file for file2.txt
    assert "file2.txt" in atomized[1].content
    # Third should be write_file
    assert "output.txt" in atomized[2].content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
