"""Error envelope parsing for 0Latency API responses.

Supports CP9 Phase 2 standardized error envelopes with code, message, hint, docs_url.
"""

import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class APIError:
    """Structured API error from envelope."""
    code: str
    message: str
    hint: str
    docs_url: str
    
    def format_for_display(self) -> str:
        """Format error for terminal display with colors."""
        # Red for error message
        lines = [f"\033[31mError: {self.message}\033[0m"]
        
        # Dim gray for hint
        if self.hint:
            lines.append(f"\033[2m💡 {self.hint}\033[0m")
        
        # Blue for docs link
        if self.docs_url:
            lines.append(f"\033[34m📖 {self.docs_url}\033[0m")
        
        return "\n".join(lines)


def parse_error_envelope(response_data: Dict[str, Any]) -> Optional[APIError]:
    """Parse error envelope from API response.
    
    Handles CP9 P2 error format: {"detail": {"error": {code, message, hint, docs_url}}}
    
    Args:
        response_data: Parsed JSON response from API
        
    Returns:
        APIError if envelope found, None for legacy/plain errors
    """
    try:
        # Check for new error envelope structure
        if "detail" in response_data and isinstance(response_data["detail"], dict):
            error_data = response_data["detail"].get("error")
            if error_data and isinstance(error_data, dict):
                return APIError(
                    code=error_data.get("code", "UNKNOWN"),
                    message=error_data.get("message", "An error occurred"),
                    hint=error_data.get("hint", ""),
                    docs_url=error_data.get("docs_url", "")
                )
        
        # Fallback: legacy plain string detail
        if "detail" in response_data and isinstance(response_data["detail"], str):
            return APIError(
                code="UNKNOWN",
                message=response_data["detail"],
                hint="",
                docs_url=""
            )
        
        return None
    except Exception:
        return None


def print_error(response_data: Dict[str, Any], status_code: int) -> None:
    """Print formatted error to stderr.
    
    Args:
        response_data: Parsed JSON response
        status_code: HTTP status code
    """
    error = parse_error_envelope(response_data)
    
    if error:
        print(error.format_for_display(), file=sys.stderr)
    else:
        # Fallback: print raw response
        print(f"API Error ({status_code}): {response_data}", file=sys.stderr)


def print_next_action(response_data: Dict[str, Any]) -> None:
    """Print next_action suggestion if present in response.
    
    Args:
        response_data: Parsed JSON response (successful 200/201)
    """
    try:
        next_action = response_data.get("next_action")
        if next_action and isinstance(next_action, dict):
            suggested_query = next_action.get("suggested_query", "")
            if suggested_query:
                print("\n\033[32m✓ Memory stored.\033[0m")
                print(f"\033[2mTry recalling it: 0latency memory recall '{suggested_query}'\033[0m")
    except Exception:
        pass  # Silently ignore - next_action is optional
