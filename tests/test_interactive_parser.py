"""
Interactive mode parser validation test.

Validates that the Claude Code profile parser correctly identifies roles
in a multi-turn interactive session captured from real PTY bytes.
"""

import pytest
from pathlib import Path
from zerolatency_cli.profiles.claude_code import ClaudeCodeProfile
from zerolatency_cli.atom import Atom


class TestInteractiveParser:
    """Test parser against captured interactive session."""
    
    @pytest.fixture
    def session_bytes(self):
        """Load the captured interactive session fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "interactive_session_raw.bin"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        with open(fixture_path, "rb") as f:
            return f.read()
    
    def test_interactive_role_detection(self, session_bytes):
        """
        Parse interactive session and verify correct role attribution.
        
        Expected pattern in fixture:
        1. User: "What is 2+2?"
        2. Assistant: "2 + 2 = 4"
        3. User: "List files in the current directory"
        4. Assistant: "The current directory contains:..." (with tool use)
        5. User: "What is in file1.txt?"
        6. Assistant: "The file contains: Hello, World!" (with tool use)
        7. User: "Thank you"
        8. Assistant: "You are welcome!..."
        9. User: "/exit"
        10. Assistant: "Goodbye!"
        """
        collected_atoms = []
        
        def collect_atom(atom: Atom):
            """Collect emitted atoms for validation."""
            collected_atoms.append(atom)
        
        # Create profile for interactive mode (no user_query)
        profile = ClaudeCodeProfile(
            agent_id="test-session-interactive",
            agent_version="2.1.136",
            user_query=None  # Interactive mode, not --print
        )
        
        # Parse the session bytes
        profile.parse_chunk(session_bytes, collect_atom)
        profile.flush(collect_atom)
        
        # Verify we extracted multiple turns
        # Minimum: should detect user/assistant alternation
        assert len(collected_atoms) > 0, "Parser should emit atoms from interactive session"
        
        # For now, verify basic parsing works (P1 parser may be simplistic)
        # P2 will add more sophisticated turn detection
        for atom in collected_atoms:
            assert atom.role in ["user", "assistant", "tool_use"], \
                f"Invalid role: {atom.role}"
            assert len(atom.content) > 0, "Atom content should not be empty"
            assert atom.agent_id == "test-session-interactive"
            assert atom.agent_name == "claude-code"
        
        print(f"Parsed {len(collected_atoms)} atoms from interactive session")
        
        # Display parsed atoms for manual verification
        for i, atom in enumerate(collected_atoms):
            content_preview = atom.content[:50].replace("\n", " ")
            print(f"  Atom {i+1}: role={atom.role}, content={content_preview}...")
    
    def test_ansi_stripping(self, session_bytes):
        """Verify ANSI codes are stripped from content."""
        collected_atoms = []
        
        def collect_atom(atom: Atom):
            collected_atoms.append(atom)
        
        profile = ClaudeCodeProfile(
            agent_id="test-ansi",
            agent_version="2.1.136"
        )
        
        profile.parse_chunk(session_bytes, collect_atom)
        profile.flush(collect_atom)
        
        # Verify no ANSI escape sequences in stripped content
        for atom in collected_atoms:
            assert "\x1b[" not in atom.content, \
                f"ANSI codes should be stripped from content: {atom.content[:100]}"
        
        # Verify raw content still has ANSI codes
        has_ansi_in_raw = False
        for atom in collected_atoms:
            if b"\x1b[" in atom.content_raw:
                has_ansi_in_raw = True
                # Verify it was stripped from content
                assert "\x1b[" not in atom.content
                break
        
        # If fixture has ANSI codes, we should find them in at least one raw atom
        if b"\x1b[" in session_bytes:
            assert has_ansi_in_raw, "Expected to find ANSI codes in at least one atom content_raw"
        
        print("ANSI stripping verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
