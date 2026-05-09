# Claude Code Profile

## Tested CLI Version

2.1.136 (Claude Code)

## Render Format Notes

Based on analysis of real captured bytes from `claude --print` mode:

### Prompt Sigil
- User prompts are preceded by: `\x1b[32m>\x1b[0m ` (green `>` followed by reset, then space)
- ANSI codes: `\x1b[32m` = green foreground, `\x1b[0m` = reset

### Response Format
- Assistant responses follow immediately after the newline from user prompt
- No explicit "assistant start" marker beyond the content itself
- Responses can contain:
  - Plain text answers
  - Code blocks delimited by triple backticks: ` ```python\n...code...\n``` `
  - Mixed text and code

### Tool Use Markers
- Tool use appears to be rendered inline (based on P1 fixture showing `\x1b[2m` dim text for actions)
- P1 example showed: `\x1b[2mListing files...\x1b[0m` and `\x1b[2mReading file1.txt...\x1b[0m`

### Turn Boundaries
- Each turn starts with the green prompt marker `\x1b[32m>\x1b[0m`
- Response ends when next prompt marker appears or EOF

### Code Blocks
- Standard markdown code fence format: ` ```language\ncode\n``` `
- Language identifier included (e.g., `python`, `javascript`, `sql`)

## Known Quirks

- Interactive mode (`claude` with no args) shows "Not logged in" auth issues even when `--print` mode works
- `--print` mode outputs plain responses without interactive styling
- ANSI codes minimal in `--print` mode compared to full interactive TTY mode

## Profile Compatibility

- Tested against Claude Code 2.1.136
- `__compat_agent_version__` should be set to `"2.1.136"`
- Fixture captured using `--print` mode for consistent non-TTY output

## Capture Method

The test fixture `tests/fixtures/cli-bytes/claude-real-session.bytes` was captured from a real interactive PTY session using the `script` command:

```bash
script -q -c "claude" /tmp/claude-interactive-capture.bytes
```

This capture includes:
- Claude Code boot banner and initialization sequence
- Full ANSI cursor positioning and color codes
- Interactive prompt markers (UTF-8 ❯ character)
- Real user input and assistant responses

### Verification

The fixture passes the following quality gates:
- File size > 5KB (actual: ~60KB)
- ANSI sequence count > 50 (actual: 474 sequences)
- Contains Claude Code boot banner or session metadata
- Includes multiple turn boundaries marked by prompt symbols

This capture method closes the CP10 P1 hygiene Task 2 interactive-validation gap. The parser (`ClaudeCodeProfile`) handles both interactive PTY captures (with `script` header/footer) and legacy `--print` mode captures.

### Parser Implementation

The `ClaudeCodeProfile` parser:
- Strips `script` command headers ("Script started on...") and footers
- Detects turn boundaries using UTF-8 ❯ (PROMPT_MARKER = `\xe2\x9d\xaf`)
- Falls back to legacy ANSI green ">" prompt pattern for `--print` mode
- Filters UI chrome (separators, status lines, prompts) from content atoms
- Implements Profile ABC interface (detect_role, is_complete_turn) for fixture testing
- Implements P1 streaming API (parse_chunk, flush) for live capture

Last updated: 2026-05-09 (CP10 P2 ADDENDUM)
