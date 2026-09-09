# macuse

![Claude Code on one machine driving a Mac through macuse](https://raw.githubusercontent.com/yunfeng-enrich/macuse/main/demo/demo.gif)

*Left: Claude Code, anywhere. Right: a Mac running `macuse up`. The agent reaches it only through the printed URL.*

Turn your Mac into a remote computer-use host. One command on the Mac, one paste into
Claude Code or Codex, and the agent can see your screen, click, type, and open apps.

Built on [CUA](https://github.com/trycua/cua)'s `computer-server` for the macOS driver.
macuse adds the parts that make it safe to reach from outside: a bearer token, a tool
allowlist that hides shell and filesystem access by default, a Cloudflare quick tunnel,
keep-awake, and a permissions preflight.

## Quick start

```
uvx macuse up
```

Or without uv installed:

```
curl -fsSL https://raw.githubusercontent.com/yunfeng-enrich/macuse/main/install.sh | sh
```

Either way macuse fetches cloudflared on first run and starts the server. It prints one line to paste into your agent, plus the one-line commands:

```
claude mcp add --transport http macuse https://<host>/<token>/mcp
codex mcp add macuse --url https://<host>/<token>/mcp
```

The token lives in the URL so no client needs custom headers. `Authorization: Bearer <token>`
against `https://<host>/mcp` works too.

## Permissions

macOS grants Screen Recording and Accessibility per app, and the app is whichever
terminal launched `macuse`. The first run triggers both prompts. Screen Recording only
takes effect after that terminal is fully quit and reopened. Without it, screenshots
are black and window titles are empty. Check with:

```
macuse check
```

## What is exposed

By default: screenshot, mouse, keyboard, clipboard, windows, app launch, and the
accessibility tree. Not exposed unless you ask:

- `--allow-shell` adds `computer_run_command`
- `--allow-files` adds file read, write, and delete tools

Other flags: `--no-tunnel` for LAN or SSH-forwarded use, `--width/--height` to scale
screenshots and coordinates for the model, `--port`, `--token`.

## Security

This is your real desktop on a public URL. The token is the only lock, and it is in the
URL, so treat the URL like a password. Both the hostname and the token are new on every
run, so a leaked URL stops working the moment you Ctrl-C. Keep the terminal visible while
an agent is connected. Pass `--token` only if you need a fixed one.

## Status

Spike. Works end to end on macOS 15 with Claude Code over a Cloudflare tunnel.
Not yet: signed menu bar app, persistent tunnel hostnames, per-app allowlists, Lume VM
sandbox mode.
