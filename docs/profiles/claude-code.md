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
