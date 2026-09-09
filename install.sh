#!/bin/sh
# Installs macuse and starts it. Usage:
#   curl -fsSL https://raw.githubusercontent.com/yunfeng-enrich/macuse/main/install.sh | sh
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "macuse runs on macOS only." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing macuse..."
uv tool install --quiet --force --python 3.12 macuse
export PATH="$HOME/.local/bin:$PATH"

# Reattach stdin to the terminal so Ctrl-C works under `curl | sh`.
if ( : </dev/tty ) 2>/dev/null; then
  exec macuse up "$@" </dev/tty
fi
exec macuse up "$@"
