"""Test Claude Code profile against real captured fixture."""

import pytest
import json
from pathlib import Path
from zerolatency_cli.profiles.claude_code import ClaudeCodeProfile
from zerolatency_cli.atom import Atom


class TestClaudeCodeProfile:
    """Test Claude Code profile against real-byte fixture from Task 2."""
    
    @pytest.fixture
    def fixture_bytes(self):
        """Load the captured Claude Code session fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "cli-bytes" / "claude-real-session.bytes"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        with open(fixture_path, "rb") as f:
            return f.read()
    
    @pytest.fixture
    def expected_atoms(self):
        """Load expected atoms for validation."""
        expected_path = Path(__file__).parent / "fixtures" / "cli-bytes" / "claude-real-session.expected-atoms.json"
        assert expected_path.exists(), f"Expected atoms not found: {expected_path}"
        with open(expected_path, "r") as f:
            return json.load(f)
    
    def test_fixture_replay(self, fixture_bytes, expected_atoms):
        """
        Replay Task 2 fixture and verify atom-by-atom correctness.
        
        This tests that the refactored ClaudeCodeProfile correctly parses
        the real 10-turn Claude Code session captured in Task 2.
        """
        collected_atoms = []
        
        def collect_atom(atom: Atom):
            """Collect emitted atoms for validation."""
            collected_atoms.append(atom)
        
        # Create profile (simulating --print mode capture)
        profile = ClaudeCodeProfile(
            agent_id="test-fixture-replay",
            agent_version="2.1.136",
            user_query=None  # Fixture is from --print mode but contains prompts
        )
        
        # Parse the fixture bytes
        profile.parse_chunk(fixture_bytes, collect_atom)
        profile.flush(collect_atom)
        
        # Verify we collected atoms
        assert len(collected_atoms) > 0, "Should emit atoms from fixture"
        
        # Verify against expected atoms
        # expected_atoms has 20 entries (10 turns × 2 roles each)
        assert len(expected_atoms) == 20, "Expected 20 atoms from 10-turn session"
        
        # Check that we have the expected content substrings
        # (Not exact match due to potential format variations)
        for expected in expected_atoms:
            turn = expected["turn"]
            role = expected["role"]
            substring = expected["content_substring"]
            
            # Find matching atom by role and content
            found = False
            for atom in collected_atoms:
                if atom.role == role and substring.lower() in atom.content.lower():
                    found = True
                    break
            
            assert found, f"Turn {turn} {role} atom with '{substring}\ not found"
        
        print(f"Validated {len(expected_atoms)} expected atoms against {len(collected_atoms)} collected atoms")
    
    def test_profile_abc_methods(self, fixture_bytes):
        """Test that Profile ABC methods work on fixture buffer."""
        profile = ClaudeCodeProfile()
        
        # Test detect_role
        atom = profile.detect_role(fixture_bytes)
        assert atom is not None, "Should detect at least one role from fixture"
        assert atom.role in ["user", "assistant"], f"Invalid role: {atom.role}"
        assert len(atom.content) > 0, "Atom content should not be empty"
        
        # Test is_complete_turn
        assert profile.is_complete_turn(fixture_bytes), "Fixture should contain complete turns"
        
        # Test extract_metadata
        metadata = profile.extract_metadata(fixture_bytes)
        assert isinstance(metadata, dict), "Metadata should be a dict"
        
        print(f"Profile ABC methods validated: role={atom.role}, complete_turn=True")
    
    def test_ansi_stripping(self, fixture_bytes):
        """Verify ANSI codes are stripped from content."""
        collected_atoms = []
        
        def collect_atom(atom: Atom):
            collected_atoms.append(atom)
        
        profile = ClaudeCodeProfile(
            agent_id="test-ansi",
            agent_version="2.1.136"
        )
        
        profile.parse_chunk(fixture_bytes, collect_atom)
        profile.flush(collect_atom)
        
        # Verify no ANSI escape sequences in stripped content
        for atom in collected_atoms:
            assert "\\x1b[" not in atom.content, \
                f"ANSI codes should be stripped: {atom.content[:100]}"
        
        # Verify raw content still has ANSI codes where present
        has_ansi_in_raw = any(b"\\x1b[" in atom.content_raw for atom in collected_atoms)
        if b"\\x1b[" in fixture_bytes:
            assert has_ansi_in_raw, "Expected ANSI codes in at least one raw atom"
        
        print(f"ANSI stripping validated across {len(collected_atoms)} atoms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
