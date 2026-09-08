import argparse
import logging
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__, permissions
from .tunnel import Tunnel

CONFIG_DIR = Path(os.environ.get("MACUSE_HOME", Path.home() / ".macuse"))
TOKEN_FILE = CONFIG_DIR / "token"


def load_or_create_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    return token


def cmd_check(args) -> int:
    p = permissions.check(prompt=args.prompt)
    print(permissions.explain(p))
    if not p.ok and args.open:
        permissions.open_pane("screen" if not p.screen_recording else "accessibility")
    return 0 if p.ok else 1


def print_connect_info(url: str, token: str) -> None:
    print()
    print(f"  MCP endpoint : {url}/mcp")
    print(f"  Token        : {token}")
    print()
    print("Claude Code:")
    print(f'  claude mcp add --transport http macuse {url}/mcp --header "Authorization: Bearer {token}"')
    print()
    print("Codex (~/.codex/config.toml):")
    print("  [mcp_servers.macuse]")
    print(f'  url = "{url}/mcp"')
    print(f'  http_headers = {{ Authorization = "Bearer {token}" }}')
    print()


def cmd_up(args) -> int:
    import uvicorn

    from .server import build_app

    p = permissions.check(prompt=True)
    print(permissions.explain(p))
    if not p.ok and not args.force:
        print("\nRefusing to start without permissions. Use --force to start anyway.")
        return 1

    token = args.token or load_or_create_token()
    app = build_app(token, shell=args.allow_shell, files=args.allow_files, width=args.width, height=args.height)

    caffeinate = None
    if shutil.which("caffeinate") and not args.no_keep_awake:
        caffeinate = subprocess.Popen(["caffeinate", "-d", "-i", "-w", str(os.getpid())])

    tunnel = None
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_tunnel:
        if not Tunnel.available():
            print("cloudflared not found. Install with `brew install cloudflared` or pass --no-tunnel.")
            return 1
        tunnel = Tunnel(args.port)
        print("\nOpening tunnel...")
        url = tunnel.start()

    print_connect_info(url, token)
    exposed = ["desktop"] + (["shell"] if args.allow_shell else []) + (["files"] if args.allow_files else [])
    print(f"Exposing: {', '.join(exposed)}. Ctrl-C to stop.\n")

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
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    logging.getLogger("fastmcp").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(prog="macuse", description="Turn this Mac into a remote computer-use host.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("up", help="start the MCP server and expose it")
    up.add_argument("--port", type=int, default=7788)
    up.add_argument("--token", help="bearer token (default: generated and saved in ~/.macuse/token)")
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
