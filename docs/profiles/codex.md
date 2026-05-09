# Codex Profile

## Tested CLI Version

codex-cli 0.130.0

## Auth Status

**BLOCKER**: Requires OpenAI API authentication. 
- CLI is installed and functional
- Running `codex exec` returns "401 Unauthorized: Missing bearer or basic authentication"
- Needs OPENAI_API_KEY environment variable or `codex login` to be configured
- Fixture capture blocked until auth is configured

## Render Format Notes

(To be populated after auth is configured and real session is captured)

## Known Quirks

(To be populated after auth is configured)

## Profile Compatibility

(To be populated after auth is configured)

**Note**: Render format analysis blocked by auth requirement. Based on CLI structure:
- Expected prompt format: likely `$ ` or similar shell-style prompt
- ANSI codes: TBD (requires real session capture)
- Example byte sequence: `\x1b[` (common ANSI escape start, to be verified)
