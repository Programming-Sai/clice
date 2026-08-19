#!/usr/bin/env bash
# clice installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/programming-sai/clice/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --with-docker   # auto-install Docker on Linux, no prompt
#   curl -fsSL .../install.sh | bash -s -- --no-docker     # never install Docker, no prompt
set -euo pipefail

REPO="programming-sai/clice"
INSTALL_DIR="$HOME/.clice/app"
BIN_DIR="$HOME/.local/bin"
WITH_DOCKER=""

for arg in "$@"; do
  case "$arg" in
    --with-docker) WITH_DOCKER="yes" ;;
    --no-docker)   WITH_DOCKER="no" ;;
  esac
done

info()  { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m==>\033[0m %s\n' "$1"; }
error() { printf '\033[1;31m==>\033[0m %s\n' "$1" >&2; }

# ── 1. Platform + arch detection ──────────────────────────────────────
case "$(uname -s)" in
  Linux*)  OS="linux" ;;
  Darwin*) OS="macos" ;;
  *)
    error "clice needs a real Unix shell (it uses pexpect, which has no native Windows equivalent)."
    error "Supported: Linux, macOS, or WSL. If you're on Windows, run this inside WSL."
    exit 1
    ;;
esac

case "$(uname -m)" in
  x86_64|amd64) ARCH="x86_64" ;;
  arm64|aarch64)
    if [ "$OS" = "linux" ]; then
      error "No prebuilt linux-arm64 binary yet - sorry. Open an issue if you need one."
      exit 1
    fi
    ARCH="arm64"
    ;;
  *) error "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

ASSET="clice-${OS}-${ARCH}"
info "Detected: $OS/$ARCH -> $ASSET"

# ── 2. Docker check - always ask before installing, unless a flag was given ──
#
# IMPORTANT: when this script runs via `curl ... | bash`, stdin is the pipe
# from curl, not the terminal - so `read` (and any `[ -t 0 ]` check) can't
# see the user's actual terminal at all. The fix used here: check `-t 1`
# (stdout, which the pipe doesn't touch) to detect an interactive run, and
# read the prompt explicitly from /dev/tty instead of stdin. Without this,
# the prompt below would either hang forever or - as originally shipped -
# silently skip itself every single time, defeating the whole point of
# asking before installing anything.
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  info "Docker is installed and running."
else
  warn "Docker was not found (or isn't running)."
  if [ "$OS" = "linux" ]; then
    DO_INSTALL="no"
    if [ "$WITH_DOCKER" = "yes" ]; then
      DO_INSTALL="yes"
    elif [ "$WITH_DOCKER" != "no" ] && [ -t 1 ] && [ -r /dev/tty ]; then
      read -r -p "Install Docker now via the official get.docker.com script (uses sudo)? [y/N] " reply < /dev/tty
      case "$reply" in
        [yY]*) DO_INSTALL="yes" ;;
      esac
    elif [ "$WITH_DOCKER" != "no" ]; then
      warn "No terminal available to ask interactively (and no --with-docker/--no-docker flag)."
      warn "Skipping Docker install - re-run with --with-docker to install it automatically."
    fi

    if [ "$DO_INSTALL" = "yes" ]; then
      info "Installing Docker via the official get.docker.com script..."
      curl -fsSL https://get.docker.com | sh
      info "Adding $USER to the docker group (so you don't need sudo for docker commands)..."
      sudo usermod -aG docker "$USER" || true
      warn "Log out and back in (or run: newgrp docker) for that group change to take effect."
    else
      warn "Skipping Docker install. clice will not work until Docker is installed and running:"
      warn "  https://docs.docker.com/engine/install/"
    fi
  else
    warn "clice needs Docker Desktop here - this script can't install a GUI app for you."
    warn "  brew install --cask docker   (then launch it once from Applications)"
  fi
fi

# ── 3. Download and extract the matching pre-built binary ────────────
LATEST_URL="https://github.com/${REPO}/releases/latest/download/${ASSET}.tar.gz"
mkdir -p "$INSTALL_DIR"
info "Downloading $ASSET..."
if ! curl -fsSL "$LATEST_URL" -o "/tmp/${ASSET}.tar.gz"; then
  error "Download failed. Is there a released build for $OS/$ARCH yet?"
  error "  $LATEST_URL"
  exit 1
fi

info "Extracting..."
tar xzf "/tmp/${ASSET}.tar.gz" -C "$INSTALL_DIR" --strip-components=0
rm -f "/tmp/${ASSET}.tar.gz"

# ── 4. Symlink the executable onto PATH ───────────────────────────────
mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/clice/clice" "$BIN_DIR/clice"
info "Installed: $BIN_DIR/clice"

case ":${PATH:-}:" in
  *":$BIN_DIR:"*)
    info "~/.local/bin is already on your PATH."
    ;;
  *)
    SHELL_RC="$HOME/.profile"
    case "${SHELL:-}" in
      */zsh)  SHELL_RC="$HOME/.zshrc" ;;
      */bash) SHELL_RC="$HOME/.bashrc" ;;
    esac
    if ! grep -q '.local/bin' "$SHELL_RC" 2>/dev/null; then
      printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$SHELL_RC"
      warn "Added ~/.local/bin to PATH in $SHELL_RC"
    fi
    warn "Open a new terminal (or run: source $SHELL_RC) before 'clice' will be found."
    ;;
esac

echo
info "Done. Try: clice doctor"