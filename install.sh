#!/usr/bin/env bash
set -euo pipefail

echo "=== MouseUtils installer (generic) ==="

INSTALL_DIR="$HOME/.mouseutils"
BIN="$INSTALL_DIR/bin/mouseutils"
USER_BIN1="$HOME/.local/bin"
USER_BIN2="$HOME/bin"

PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3 is required but not found." >&2
  exit 1
fi

# 1) Create venv and install
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Creating venv at $INSTALL_DIR..."
  "$PYTHON_BIN" -m venv "$INSTALL_DIR"
fi

# shellcheck disable=SC1091
source "$INSTALL_DIR/bin/activate"
pip install -U pip wheel setuptools
# From GitHub:
pip install -U git+https://github.com/panadalpro/mouseutils.git@main

deactivate

# 2) Make sure user bin dirs exist
mkdir -p "$USER_BIN1" "$USER_BIN2"

# 3) Prefer a symlink in ~/.local/bin (no PATH edits if ya está en PATH)
if [ -x "$BIN" ]; then
  ln -sf "$BIN" "$USER_BIN1/mouseutils"
  echo "Linked $BIN -> $USER_BIN1/mouseutils"
fi

# 4) Helper to test membership in PATH (robusto)
in_path() {
  case ":$PATH:" in *":$1:"*) return 0 ;; *) return 1 ;; esac
}

# 5) Compute PATH lines we want to ensure
LINE1='export PATH="$HOME/.local/bin:$PATH"'
LINE2='export PATH="$HOME/bin:$PATH"'
LINE3='export PATH="$HOME/.mouseutils/bin:$PATH"'  # fallback directo al venv

add_line_if_missing() {
  local file="$1" line="$2"
  [ -f "$file" ] || touch "$file"
  grep -qsF "$line" "$file" || { printf '\n# mouseutils\n%s\n' "$line" >> "$file"; echo "Updated $file"; }
}

# 6) Persistently add to rc files (cross-shell):
#    - POSIX profile
add_line_if_missing "$HOME/.profile" "$LINE1"
add_line_if_missing "$HOME/.profile" "$LINE2"
#    - If bash present
[ -n "${BASH_VERSION-}" ] || [ -f "$HOME/.bashrc" ] && add_line_if_missing "$HOME/.bashrc" "$LINE1"
[ -n "${BASH_VERSION-}" ] || [ -f "$HOME/.bashrc" ] && add_line_if_missing "$HOME/.bashrc" "$LINE2"
[ -f "$HOME/.bash_profile" ] && { add_line_if_missing "$HOME/.bash_profile" "$LINE1"; add_line_if_missing "$HOME/.bash_profile" "$LINE2"; }
#    - If zsh present (macOS default)
[ -n "${ZSH_VERSION-}" ] || [ -f "$HOME/.zshrc" ] && add_line_if_missing "$HOME/.zshrc" "$LINE1"
[ -n "${ZSH_VERSION-}" ] || [ -f "$HOME/.zshrc" ] && add_line_if_missing "$HOME/.zshrc" "$LINE2"
[ -f "$HOME/.zprofile" ] && { add_line_if_missing "$HOME/.zprofile" "$LINE1"; add_line_if_missing "$HOME/.zprofile" "$LINE2"; }

# 7) Export for current subshell (no garantiza tu shell padre si haces curl|bash)
export PATH="$HOME/.local/bin:$HOME/bin:$INSTALL_DIR/bin:$PATH"

echo
echo "Installed."
echo
echo "Try now in THIS terminal:"
echo "  mouseutils  ||  $USER_BIN1/mouseutils"
echo
echo "If 'command not found', do ONE of these:"
echo "  1) bash/zsh:   source ~/.profile; [ -f ~/.zshrc ] && source ~/.zshrc; [ -f ~/.bashrc ] && source ~/.bashrc; hash -r || rehash"
echo "  2) Close and reopen your terminal"
echo
# If we ARE being sourced, also enable immediately:
# Detect if sourced (bash: $0 = bash; zsh: $ZSH_EVAL_CONTEXT ends with :file)
if (return 0 2>/dev/null); then
  echo "(Detected: script is sourced) PATH now is:"
  echo "$PATH"
else
  echo "(Note: running via a subshell cannot change your parent shell's PATH immediately.)"
  echo "To make it instant next time, run the installer with:"
  echo "  source <(curl -fsSL https://.../install.sh)   # bash/zsh"
fi
