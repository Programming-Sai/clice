#!/usr/bin/env bash
# clice uninstaller
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/programming-sai/clice/main/uninstall.sh | bash
#   curl -fsSL .../uninstall.sh | bash -s -- --keep-settings   # keep ~/.clice/settings.json and history
set -euo pipefail

print_help() {
  cat << 'EOF'
clice uninstaller

Usage:
  curl -fsSL https://raw.githubusercontent.com/programming-sai/clice/main/uninstall.sh | bash
  curl -fsSL .../uninstall.sh | bash -s -- [options]

Options:
  --keep-settings   Remove the binary only; keep ~/.clice/settings.json,
                     session history, and the local registry cache
  -h, --help        Show this help and exit

What it removes (without --keep-settings):
  ~/.local/bin/clice   the symlinked executable
  ~/.clice/app         the installed binary + bundled runtime
  ~/.clice             settings, session history, local registry cache

What it does NOT touch:
  Docker itself, even if install.sh installed it for you - that's a
  separate, bigger decision left up to you.

From inside an existing install, `clice uninstall` does the same thing.
EOF
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) print_help; exit 0 ;;
  esac
done

INSTALL_DIR="$HOME/.clice/app"
BIN_LINK="$HOME/.local/bin/clice"
KEEP_SETTINGS="no"

for arg in "$@"; do
  case "$arg" in
    --keep-settings) KEEP_SETTINGS="yes" ;;
  esac
done

info() { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m==>\033[0m %s\n' "$1"; }

# Mirrors exactly what install.sh creates - nothing more, nothing less.
# It does NOT touch Docker itself, even if install.sh installed it for
# you, since removing a system-wide Docker install is a much bigger,
# separate decision than uninstalling clice.

if [ -L "$BIN_LINK" ] || [ -f "$BIN_LINK" ]; then
  rm -f "$BIN_LINK"
  info "Removed $BIN_LINK"
else
  warn "$BIN_LINK not found (already removed, or never installed here)"
fi

if [ -d "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  info "Removed $INSTALL_DIR (the binary + bundled runtime)"
fi

if [ "$KEEP_SETTINGS" = "yes" ]; then
  warn "Keeping ~/.clice/settings.json and ~/.clice/cache (--keep-settings) - only the binary itself was removed."
else
  if [ -d "$HOME/.clice" ]; then
    rm -rf "$HOME/.clice"
    info "Removed ~/.clice (settings, session history, local registry cache)"
  fi
fi

echo
info "clice has been uninstalled."
info "Note: this does not remove Docker, even if install.sh installed it for you - that's a separate, bigger decision left up to you."