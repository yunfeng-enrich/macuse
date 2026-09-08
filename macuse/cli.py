import argparse
import logging
import os
import secrets
import shutil
import subprocess
import sys
import warnings

from . import __version__, permissions
from .tunnel import Tunnel



def cmd_check(args) -> int:
    p = permissions.check(prompt=args.prompt)
    print(permissions.explain(p))
    if not p.ok and args.open:
        permissions.open_pane("screen" if not p.screen_recording else "accessibility")
    return 0 if p.ok else 1


def print_connect_info(url: str, token: str, tool_count: int, exposed: list[str], local: str) -> None:
    from rich.console import Console
    from rich.text import Text

    # soft_wrap keeps every command on one logical line, so a terminal copy yields no newlines.
    console = Console(soft_wrap=True)
    endpoint = f"{url}/{token}/mcp"

    console.print()
    console.print(Text.assemble(("  macuse ", "bold green"), ("ready", "green"), ("   ", ""),
                                (f"{tool_count} tools", "dim"), ("  ·  ", "dim"), (", ".join(exposed), "dim")))
    console.print()
    console.print(Text("  Paste into Claude Code, Codex, or any MCP agent", style="bold cyan"))
    console.print(Text(f'  Add an MCP server named "macuse" using streamable HTTP at {endpoint} '
                       "then take a screenshot with it and tell me what is on my Mac's screen."))
    console.print()
    console.print(Text("  Or add it yourself", style="bold"))
    console.print(Text(f"  claude mcp add --transport http macuse {endpoint}", style="cyan"))
    console.print(Text(f"  codex mcp add macuse --url {endpoint}", style="cyan"))
    console.print()
    console.print(Text.assemble(("  local ", "dim"), (local, ""), ("   ·   Ctrl-C to stop", "dim")))
    console.print()


def cmd_up(args) -> int:
    import uvicorn

    from .server import build_app

    p = permissions.check(prompt=True)
    if not p.ok:
        print(permissions.explain(p))
        if not args.force:
            print("\nRefusing to start without permissions. Use --force to start anyway.")
            return 1

    # Fresh token per run: the tunnel hostname changes each run anyway, and a leaked URL dies on Ctrl-C.
    token = args.token or secrets.token_urlsafe(16)
    app, tool_count = build_app(token, shell=args.allow_shell, files=args.allow_files, width=args.width, height=args.height)

    caffeinate = None
    if shutil.which("caffeinate") and not args.no_keep_awake:
        caffeinate = subprocess.Popen(["caffeinate", "-d", "-i", "-w", str(os.getpid())])

    tunnel = None
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_tunnel:
        tunnel = Tunnel(args.port)
        print("Opening tunnel...", flush=True)
        url = tunnel.start()

    exposed = ["desktop"] + (["shell"] if args.allow_shell else []) + (["files"] if args.allow_files else [])
    print_connect_info(url, token, tool_count, exposed, f"http://127.0.0.1:{args.port}")

    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    except KeyboardInterrupt:
        pass
    finally:
        if tunnel:
            tunnel.stop()
        if caffeinate:
            caffeinate.terminate()
    return 0


def main(argv=None) -> None:
    sys.stdout.reconfigure(line_buffering=True)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    for noisy in ("fastmcp", "mcp", "uvicorn"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(prog="macuse", description="Turn this Mac into a remote computer-use host.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("up", help="start the MCP server and expose it")
    up.add_argument("--port", type=int, default=7788)
    up.add_argument("--token", help="use a fixed token instead of a fresh one per run")
    up.add_argument("--no-tunnel", action="store_true", help="local only, skip cloudflared")
    up.add_argument("--allow-shell", action="store_true", help="also expose computer_run_command")
    up.add_argument("--allow-files", action="store_true", help="also expose file read/write/delete tools")
    up.add_argument("--width", type=int, help="scale screenshots and coordinates to this width")
    up.add_argument("--height", type=int, help="scale screenshots and coordinates to this height")
    up.add_argument("--no-keep-awake", action="store_true")
    up.add_argument("--force", action="store_true", help="start even if permissions are missing")
    up.set_defaults(fn=cmd_up)

    check = sub.add_parser("check", help="show macOS permission status")
    check.add_argument("--prompt", action="store_true", help="trigger the system permission dialogs")
    check.add_argument("--open", action="store_true", help="open the relevant System Settings pane")
    check.set_defaults(fn=cmd_check)

    args = parser.parse_args(argv)
    sys.exit(args.fn(args))
