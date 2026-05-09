# Task 2 - Fixture Capture Blockers

## Summary

Task 2 requires capturing real-byte fixtures from four agents: Claude Code, Codex, Gemini CLI, and Aider.

**Status**: Partial completion - 1 of 4 agents fully captured.

## Completed

### Claude Code ✓
- **Status**: COMPLETE
- **Fixture**: `tests/fixtures/cli-bytes/claude-real-session.bytes` (1955 bytes)
- **Expected Atoms**: `tests/fixtures/cli-bytes/claude-real-session.expected-atoms.json` (20 atoms, 10 turns)
- **Auth**: Working via existing credentials
- **Method**: Used `claude --print` mode for 10 prompts

## Blocked - Awaiting Auth

### Codex ✗
- **Status**: BLOCKED - Requires OpenAI API Key
- **Error**: `401 Unauthorized: Missing bearer or basic authentication`
- **Fix Needed**: Set `OPENAI_API_KEY` environment variable or run `codex login`
- **Documented**: `docs/profiles/codex.md`

### Gemini CLI ✗
- **Status**: BLOCKED - Requires Google/Gemini API Key
- **Error**: `Please set an Auth method in your /root/.gemini/settings.json`
- **Fix Needed**: Set `GEMINI_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`, or `GOOGLE_GENAI_USE_GCA`
- **Documented**: `docs/profiles/gemini-cli.md`

### Aider ✗
- **Status**: BLOCKED - Requires LLM API Key
- **Error**: `No LLM model was specified and no API keys were provided`
- **Fix Needed**: Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or configure OpenRouter
- **Documented**: `docs/profiles/aider.md`

## Decision

Per scope guidance: "Document the blocker in `docs/profiles/<agent>.md`, continue with the remaining agents, return when fixable."

**Proceeding to Task 3 and Phase B with Claude Code as the reference implementation.** The other three profiles will be completed when API keys are configured.

## Impact on Phase B

- Task 5 (ClaudeCodeProfile): Can proceed ✓
- Task 6 (CodexProfile): Implementation possible, but cannot test against real fixtures
- Task 7 (GeminiCliProfile): Implementation possible, but cannot test against real fixtures
- Task 8 (AiderProfile): Implementation possible, but cannot test against real fixtures
- Task 9 (GenericProfile): Can proceed using Python REPL or other no-auth tool ✓

## Return Path

When API keys become available:
1. Run the capture scripts for Codex, Gemini, Aider
2. Create expected-atoms.json for each
3. Update profile docs with render format analysis
4. Test the profiles against real fixtures
5. Update Gate G2 verification
