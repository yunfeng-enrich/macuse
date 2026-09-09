"""Render Claude Code's stream-json output as a compact agent log for the demo recording."""
import json
import sys

DIM, CYAN, GREEN, BOLD, RESET = "\033[2m", "\033[36m", "\033[32m", "\033[1m", "\033[0m"

for line in sys.stdin:
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("type") == "assistant":
        for blk in ev["message"].get("content", []):
            if blk.get("type") == "tool_use":
                if not blk["name"].startswith("mcp__macuse__"):
                    continue
                name = blk["name"].replace("mcp__macuse__computer_", "")
                args = {k: v for k, v in blk.get("input", {}).items()}
                arg_s = ", ".join(f"{k}={v!r}" if not isinstance(v, str) else f"{k}={v[:40]!r}" for k, v in args.items())
                print(f"  {CYAN}▸ {name}{RESET} {DIM}{arg_s}{RESET}", flush=True)
            elif blk.get("type") == "text" and blk["text"].strip():
                print(f"\n{blk['text'].strip()}\n", flush=True)
    elif ev.get("type") == "result":
        print(f"{GREEN}✓ done{RESET} {DIM}{ev.get('duration_ms', 0) // 1000}s{RESET}", flush=True)
