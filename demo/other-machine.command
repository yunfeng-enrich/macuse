#!/bin/zsh
# The agent side of the demo: add the Mac as an MCP server, then let Claude Code use it.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT
printf '\033]50;SetProfile=Pro\a'
printf '\033]0;Claude Code\a'
URL=$(cat /tmp/vm-mcp-url)
PROMPT="Take a screenshot of my Mac and tell me in one sentence what is on screen. Then open Safari to https://github.com/yunfeng-enrich/macuse and confirm with a screenshot."
rm -f /tmp/demo-done
sleep 7
printf "\033[2J\033[3J\033[H\n"
sleep 2
printf '\033[2m# paste the line macuse printed\033[0m\n'
printf '$ claude mcp add --transport http macuse \\\n    %s\n' "$URL"
claude mcp remove -s user macuse >/dev/null 2>&1
claude mcp add -s user --transport http macuse "$URL" >/dev/null 2>&1 && printf '\033[32mAdded HTTP MCP server macuse\033[0m\n\n'
sleep 3
printf '$ claude -p "%s"\n\n' "$PROMPT"
claude -p "$PROMPT" --allowedTools "mcp__macuse__*" --disallowedTools "Bash,Edit,Write,Read,WebFetch,WebSearch" \
  --output-format stream-json --verbose 2>/dev/null | python3 "$HOME/code/macuse/demo/agentlog.py"
sleep 8
touch /tmp/demo-done
