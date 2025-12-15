#!/usr/bin/env bash
# git-adr installation script
# Usage: ./install.sh [--local] [--system] [--man-only]
#
# Installs the git-adr command via pip/uv.
# Man pages and completions are included in the tarball for reference.
#
# This follows the git-lfs installation pattern.

set -eu

prefix="/usr/local"

if [ "${PREFIX:-}" != "" ]; then
    prefix=${PREFIX:-}
fi

man_only=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --local)
            prefix="$HOME/.local"
            shift
            ;;
        --system)
            prefix="/usr/local"
            shift
            ;;
        --man-only)
            man_only=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --local     Install to ~/.local (no sudo required)"
            echo "  --system    Install to /usr/local (default, may need sudo)"
            echo "  --man-only  Only install man pages (skip Python package)"
            echo "  --help      Show this help"
            echo ""
            echo "Environment:"
            echo "  PREFIX      Override installation prefix"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install Python package (unless --man-only)
if [ "$man_only" = false ]; then
    echo "==> Installing git-adr..."
    if command -v uv >/dev/null 2>&1; then
        uv tool install git-adr || uv pip install git-adr || pip install git-adr
    elif command -v pip >/dev/null 2>&1; then
        pip install git-adr
    else
        echo "Error: Neither uv nor pip found." >&2
        echo "Install pip: https://pip.pypa.io/en/stable/installation/" >&2
        exit 1
    fi
fi

# Install man pages if present and prefix is writable
if [ -d "$SCRIPT_DIR/man" ]; then
    if [ -w "$prefix" ] || [ -w "$(dirname "$prefix")" ]; then
        echo "==> Installing man pages to $prefix/share/man..."
        mkdir -p "$prefix/share/man/man1"
        cp -r "$SCRIPT_DIR/man/man1/"* "$prefix/share/man/man1/" 2>/dev/null || true
    else
        echo "Note: Cannot write to $prefix. Man pages not installed."
        echo "      Run with sudo or use --local flag."
    fi
fi

# Install completions if present and prefix is writable
if [ -d "$SCRIPT_DIR/completions" ]; then
    if [ -w "$prefix" ] || [ -w "$(dirname "$prefix")" ]; then
        echo "==> Installing shell completions..."

        # Bash
        if [ -f "$SCRIPT_DIR/completions/git-adr.bash" ]; then
            mkdir -p "$prefix/share/bash-completion/completions"
            cp "$SCRIPT_DIR/completions/git-adr.bash" "$prefix/share/bash-completion/completions/git-adr"
        fi

        # Zsh
        if [ -f "$SCRIPT_DIR/completions/_git-adr" ]; then
            mkdir -p "$prefix/share/zsh/site-functions"
            cp "$SCRIPT_DIR/completions/_git-adr" "$prefix/share/zsh/site-functions/"
        fi

        # Fish
        if [ -f "$SCRIPT_DIR/completions/git-adr.fish" ]; then
            mkdir -p "$prefix/share/fish/vendor_completions.d"
            cp "$SCRIPT_DIR/completions/git-adr.fish" "$prefix/share/fish/vendor_completions.d/"
        fi
    fi
fi

# Set up git alias
if [ "$man_only" = false ]; then
    echo "==> Setting up git alias..."
    git config --global alias.adr '!git-adr' 2>/dev/null || true
fi

# Verify installation
if [ "$man_only" = false ]; then
    PATH+=":$prefix/bin"
    if command -v git-adr >/dev/null 2>&1; then
        echo ""
        echo "git-adr installed successfully!"
        git-adr --version
        echo ""
        echo "Quick start:"
        echo "  git adr init              # Initialize in a repository"
        echo "  git adr new 'Title'       # Create an ADR"
        echo "  git adr list              # List all ADRs"
    else
        echo ""
        echo "Note: git-adr may not be in PATH. Add to your shell config:"
        echo "  export PATH=\"\$PATH:\$HOME/.local/bin\""
    fi
fi
