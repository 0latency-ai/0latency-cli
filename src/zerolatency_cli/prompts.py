"""Interactive prompt detection heuristics."""

import re


def is_interactive_prompt(data: bytes) -> bool:
    """
    Detect if data appears to be an interactive prompt (Y/N, password, etc.).
    
    Interactive prompts are passed through transparently and NOT captured as atoms.
    
    Args:
        data: Raw bytes from PTY output
        
    Returns:
        True if data appears to be an interactive prompt
    """
    try:
        # Decode to text for pattern matching
        text = data.decode('utf-8', errors='ignore')
    except:
        return False
    
    # Strip ANSI codes for pattern matching
    ansi_pattern = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
    text_clean = ansi_pattern.sub('', text).strip()
    
    if not text_clean:
        return False
    
    text_lower = text_clean.lower()
    
    # Common interactive prompt patterns
    patterns = [
        r'\[[yn]/[yn]\]',  # [Y/n] or [y/N] (case-insensitive after lowering)
        r'\([yn]/[yn]\)',  # (Y/n) or (y/N)
        r'password:\s*$',  # password prompts (ending)
        r'passphrase:\s*$',
        r'enter\s+password',
        r'confirm.*\?\s*$',  # confirmation prompts
        r'continue.*\?\s*$',
        r'proceed.*\?\s*$',
    ]
    
    # Check for pattern matches
    for pattern in patterns:
        if re.search(pattern, text_lower):
            # Additional check: should end with '?', ':', or prompt marker
            if text_clean.rstrip().endswith(('?', ':', '? ', ': ', ')')):
                return True
    
    return False
