"""Cloudflare quick tunnel: no account, random *.trycloudflare.com hostname per run."""

import re
import shutil
import subprocess
import threading
import time

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


class Tunnel:
    def __init__(self, port: int):
        self.port = port
        self.proc: subprocess.Popen | None = None
        self.url: str | None = None

    @staticmethod
    def available() -> bool:
        return shutil.which("cloudflared") is not None

    def start(self, timeout: float = 30) -> str:
        self.proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.port}"],
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
