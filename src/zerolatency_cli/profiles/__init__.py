"""Profile registry for agent-specific parsers."""

import os
import importlib.util
from pathlib import Path
from typing import Optional
from zerolatency_cli.profiles.base import Profile


# Map of agent CLI binary names to profile module names
AGENT_TO_PROFILE = {
    "claude": "claude_code",
    "codex": "codex",
    "gemini": "gemini_cli",
    "aider": "aider",
}


def load_profile(agent_name: str) -> Optional[Profile]:
    """
    Load a profile for the given agent.
    
    Priority:
    1. User override at ~/.0latency/profiles/<agent_name>.py
    2. Built-in profile at zerolatency_cli/profiles/<agent_name>.py
    3. GenericProfile fallback
    
    Args:
        agent_name: Name of the agent (e.g., "claude", "codex")
        
    Returns:
        Profile instance, or GenericProfile if agent is unknown
    """
    # Normalize agent name to profile name
    profile_name = AGENT_TO_PROFILE.get(agent_name, "generic")
    
    # Check for user override
    user_profile_path = Path.home() / ".0latency" / "profiles" / f"{profile_name}.py"
    if user_profile_path.exists():
        return _load_profile_from_file(user_profile_path, profile_name)
    
    # Load built-in profile
    try:
        module = importlib.import_module(f"zerolatency_cli.profiles.{profile_name}")
        profile_class = getattr(module, f"{_to_class_name(profile_name)}Profile")
        return profile_class()
    except (ImportError, AttributeError):
        # Fall back to generic
        from zerolatency_cli.profiles.generic import GenericProfile
        return GenericProfile()


def _load_profile_from_file(file_path: Path, profile_name: str) -> Optional[Profile]:
    """Load a profile from a Python file."""
    try:
        spec = importlib.util.spec_from_file_location(profile_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            profile_class = getattr(module, f"{_to_class_name(profile_name)}Profile")
            return profile_class()
    except Exception:
        pass
    return None


def _to_class_name(profile_name: str) -> str:
    """
    Convert profile name to class name.
    
    Examples:
        claude_code -> ClaudeCode
        gemini_cli -> GeminiCli
        generic -> Generic
    """
    return "".join(word.capitalize() for word in profile_name.split("_"))


__all__ = ["Profile", "load_profile", "AGENT_TO_PROFILE"]
