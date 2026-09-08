"""Wraps CUA's computer-server MCP tools in bearer auth and a tool allowlist."""

import asyncio
import logging
import secrets

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send

from . import tools as tool_profiles

log = logging.getLogger("macuse")


class TokenAuth:
    """Accepts either `Authorization: Bearer <token>` or the token as the first path
    segment (https://host/<token>/mcp), so clients that cannot set headers still work."""

    def __init__(self, app: ASGIApp, token: str):
        self.app = app
        self.token = token
        self.prefix = f"/{token}"

    @staticmethod
    def _rewrite(scope: Scope, path: str) -> Scope:
        # A bare /mcp would make Starlette redirect to /mcp/, which drops the token prefix.
        if path == "/mcp":
            path = "/mcp/"
        return dict(scope, path=path, raw_path=path.encode())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] == "/health":
            return await self.app(scope, receive, send)
        path = scope["path"]
        if path.startswith(self.prefix + "/") and secrets.compare_digest(path[: len(self.prefix)], self.prefix):
            return await self.app(self._rewrite(scope, path[len(self.prefix):]), receive, send)
        auth = dict(scope["headers"]).get(b"authorization", b"").decode()
        if secrets.compare_digest(auth, f"Bearer {self.token}"):
            return await self.app(self._rewrite(scope, path), receive, send)
        resp = JSONResponse({"error": "unauthorized"}, status_code=401)
        return await resp(scope, receive, send)


def build_mcp(shell: bool, files: bool, width: int | None, height: int | None):
    from computer_server import mcp_server

    if width and height:
        mcp_server._configure_scaling(width, height)
    mcp = mcp_server.create_mcp_server()
    keep = tool_profiles.allowed(shell=shell, files=files)
    registered = {t.name for t in asyncio.run(mcp.list_tools())}
    for name in registered - keep:
        mcp.local_provider.remove_tool(name)
    log.debug("exposing %d tools (%d hidden)", len(registered & keep), len(registered - keep))
    return mcp, len(registered & keep)


def build_app(token: str, shell: bool = False, files: bool = False, width: int | None = None, height: int | None = None) -> tuple[ASGIApp, int]:
    mcp, tool_count = build_mcp(shell, files, width, height)
    mcp_app = mcp.http_app(path="/")

    async def health(_: Request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/health", health), Mount("/mcp", mcp_app)], lifespan=mcp_app.lifespan)
    return TokenAuth(app, token), tool_count
