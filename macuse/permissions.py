"""macOS TCC checks. Screen Recording and Accessibility are granted per app bundle,
so the prompt names whichever app owns this process (Terminal, iTerm, Conductor...)."""

import subprocess
import sys
from dataclasses import dataclass

SCREEN_PANE = "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
AX_PANE = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"


@dataclass
class Permissions:
    screen_recording: bool
    accessibility: bool

    @property
    def ok(self) -> bool:
        return self.screen_recording and self.accessibility


def check(prompt: bool = False) -> Permissions:
    if sys.platform != "darwin":
        return Permissions(True, True)
    import Quartz
    from ApplicationServices import AXIsProcessTrusted, AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt

    if prompt:
        screen = bool(Quartz.CGRequestScreenCaptureAccess())
        ax = bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}))
    else:
        screen = bool(Quartz.CGPreflightScreenCaptureAccess())
        ax = bool(AXIsProcessTrusted())
    return Permissions(screen, ax)


def responsible_app() -> str:
    """Walk the parent chain to the .app bundle macOS will attribute the prompt to."""
    import os

    pid = os.getpid()
    last = "your terminal"
    for _ in range(20):
        out = subprocess.run(["ps", "-o", "ppid=,comm=", "-p", str(pid)], capture_output=True, text=True).stdout.split(None, 1)
        if len(out) < 2:
            break
        ppid, comm = out[0].strip(), out[1].strip()
        if ".app/" in comm:
            last = comm.split(".app/")[0].rsplit("/", 1)[-1] + ".app"
        if ppid in ("0", "1", ""):
            break
        pid = int(ppid)
    return last


def open_pane(which: str) -> None:
    subprocess.run(["open", SCREEN_PANE if which == "screen" else AX_PANE], check=False)


def explain(p: Permissions) -> str:
    app = responsible_app()
    lines = [f"macOS permissions for {app}:"]
    lines.append(f"  Screen Recording  {'ok' if p.screen_recording else 'MISSING (screenshots will be black)'}")
    lines.append(f"  Accessibility     {'ok' if p.accessibility else 'MISSING (clicks and typing will be ignored)'}")
    if not p.ok:
        lines.append("")
        lines.append(f"Grant both to {app} in System Settings > Privacy & Security, then rerun.")
        lines.append("Screen Recording changes need the app fully quit and reopened.")
    return "\n".join(lines)
