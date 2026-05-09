"""Test Generic profile against Python REPL fixture."""

import pytest
from pathlib import Path
from zerolatency_cli.profiles.generic import GenericProfile
from zerolatency_cli.atom import Atom


class TestGenericProfile:
    """Test Generic profile with Python REPL as example unknown agent."""
    
    @pytest.fixture
    def repl_fixture(self):
        """Load Python REPL fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "cli-bytes" / "python-repl-test.bytes"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        with open(fixture_path, "rb") as f:
            return f.read()
    
    def test_generic_parse_repl(self, repl_fixture):
        """
        Test that GenericProfile can parse Python REPL output.
        
        Verifies:
        - Produces at least one atom per interactive turn
        - Atoms are tagged as user or assistant
        - No tool_use atoms (generic makes no tool inference)
        """
        collected_atoms = []
        
        def collect_atom(atom: Atom):
            collected_atoms.append(atom)
        
        profile = GenericProfile(
            agent_id="test-generic-repl",
            agent_version="python-3.12"
        )
        
        # Parse the fixture
        profile.parse_chunk(repl_fixture, collect_atom)
        profile.flush(collect_atom)
        
        # Verify we got atoms
        assert len(collected_atoms) >= 1, "Should emit at least one atom"
        
        # Verify all atoms are user or assistant (no tool_use)
        for atom in collected_atoms:
            assert atom.role in ["user", "assistant"],                 f"Generic profile should only emit user/assistant, got: {atom.role}"
            assert atom.agent_name == "generic"
            assert atom.agent_id == "test-generic-repl"
        
        # Verify no tool_use atoms
        tool_atoms = [a for a in collected_atoms if a.role == "tool_use"]
        assert len(tool_atoms) == 0, "Generic profile should not infer tool use"
        
        print(f"Parsed {len(collected_atoms)} atoms from Python REPL fixture")
    
    def test_profile_abc_methods(self, repl_fixture):
        """Test Profile ABC methods work on generic fixture."""
        profile = GenericProfile()
        
        # Test detect_role
        atom = profile.detect_role(repl_fixture)
        if atom:  # May be None if fixture is empty
            assert atom.role in ["user", "assistant"]
            assert len(atom.content) > 0
        
        # Test is_complete_turn
        assert profile.is_complete_turn(repl_fixture),             "Non-empty fixture should be complete turn"
        
        # Test extract_metadata
        metadata = profile.extract_metadata(repl_fixture)
        assert isinstance(metadata, dict)
        assert metadata.get("agent_type") == "generic"
        assert metadata.get("detection_method") == "idle-threshold"
        
        print("Profile ABC methods validated for GenericProfile")
    
    def test_empty_buffer_handling(self):
        """Test that empty buffers are handled gracefully."""
        profile = GenericProfile()
        
        # Empty buffer
        atom = profile.detect_role(b"")
        assert atom is None, "Empty buffer should return None"
        
        # Whitespace only
        atom = profile.detect_role(b"   \n  \n  ")
        assert atom is None, "Whitespace-only buffer should return None"
        
        print("Empty buffer handling validated")
    
    def test_no_role_inference(self, repl_fixture):
        """
        Verify GenericProfile makes minimal assumptions.
        
        Unlike agent-specific profiles, generic should not:
        - Parse tool calls
        - Detect code blocks specially
        - Make assumptions about turn structure
        """
        collected_atoms = []
        
        def collect_atom(atom: Atom):
            collected_atoms.append(atom)
        
        profile = GenericProfile(agent_id="test-minimal")
        profile.parse_chunk(repl_fixture, collect_atom)
        profile.flush(collect_atom)
        
        # All atoms should be simple user/assistant
        roles = set(atom.role for atom in collected_atoms)
        assert roles.issubset({"user", "assistant"}),             f"Generic profile should only use user/assistant roles, got: {roles}"
        
        # No tool_payload should be set
        for atom in collected_atoms:
            assert atom.tool_payload is None,                 "Generic profile should not set tool_payload"
        
        print("Minimal role inference verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
