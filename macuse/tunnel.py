"""Cloudflare quick tunnel: no account, random *.trycloudflare.com hostname per run.
If cloudflared is not installed, fetch the official release binary into ~/.macuse/bin."""

import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
BIN_DIR = Path(os.environ.get("MACUSE_HOME", Path.home() / ".macuse")) / "bin"
RELEASE = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-{arch}.tgz"


def ensure_binary() -> str:
    found = shutil.which("cloudflared") or shutil.which("cloudflared", path=str(BIN_DIR))
    if found:
        return found
    if sys.platform != "darwin":
        raise RuntimeError("cloudflared not found. Install it from https://github.com/cloudflare/cloudflared/releases")
    arch = "arm64" if platform.machine() == "arm64" else "amd64"
    url = RELEASE.format(arch=arch)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading cloudflared ({arch})...", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "cloudflared.tgz"
        urllib.request.urlretrieve(url, archive)
        with tarfile.open(archive) as tar:
            tar.extract("cloudflared", path=tmp)
        target = BIN_DIR / "cloudflared"
        shutil.move(Path(tmp) / "cloudflared", target)
        target.chmod(0o755)
    return str(target)


class Tunnel:
    def __init__(self, port: int):
        self.port = port
        self.proc: subprocess.Popen | None = None
        self.url: str | None = None

    def start(self, timeout: float = 30) -> str:
        binary = ensure_binary()
        self.proc = subprocess.Popen(
            [binary, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.port}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        found = threading.Event()

        def pump():
            assert self.proc and self.proc.stderr
            for line in self.proc.stderr:
                m = URL_RE.search(line)
                if m and not self.url:
                    self.url = m.group(0)
                    found.set()

        threading.Thread(target=pump, daemon=True).start()
        if not found.wait(timeout):
            self.stop()
            raise RuntimeError("cloudflared did not report a tunnel URL in time")
        # Quick tunnels take a few seconds to route after the URL is printed.
        time.sleep(2)
        return self.url  # type: ignore[return-value]

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
