# Demo

`demo.gif` and `demo.mp4` were recorded end to end with no human at either keyboard.

- The Mac on the right is a macOS VM created with [Lume](https://github.com/trycua/cua/tree/main/libs/lume),
  running `macuse up`. macuse detected the CuaDriver daemon in the image and used it, so
  no permission prompts were needed.
- The agent on the left is Claude Code on another machine, connected only through the
  public tunnel URL that macuse printed. `other-machine.command` is the exact script it ran,
  and `agentlog.py` renders Claude Code's stream-json output as the compact log you see.
- `winrec.py` captures the two windows by window ID at 8 fps, so nothing else on the
  recording machine can appear in frame, and `compose.py` lays the frames side by side.
