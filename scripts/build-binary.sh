#!/usr/bin/env bash
# Build git-adr standalone binary using PyInstaller
#
# Usage:
#   ./scripts/build-binary.sh [--clean]
#
# Options:
#   --clean    Remove existing build artifacts before building
#
# Output:
#   dist/git-adr    The standalone executable
#
# Requirements:
#   - Python 3.11+
#   - Rust (for tiktoken)
#   - libsodium (for PyNaCl, optional)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Parse arguments
CLEAN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Clean if requested
if [[ "$CLEAN" == "true" ]]; then
    info "Cleaning previous build artifacts..."
    rm -rf build/ dist/ *.spec 2>/dev/null || true
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    error "Python $REQUIRED_VERSION+ required, found $PYTHON_VERSION"
fi

info "Using Python $PYTHON_VERSION"

# Check for Rust (needed for tiktoken)
if ! command -v rustc &> /dev/null; then
    warn "Rust not found. tiktoken may fail to build."
    warn "Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
fi

# Create or activate virtual environment
VENV_DIR="$PROJECT_ROOT/.venv-build"

if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating build virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

info "Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Upgrade pip
info "Upgrading pip..."
pip install --quiet --upgrade pip

# Install dependencies
info "Installing git-adr with all extras..."
pip install --quiet -e ".[all]"

# Install PyInstaller
info "Installing PyInstaller..."
pip install --quiet pyinstaller

# Build the binary
info "Building binary with PyInstaller..."
pyinstaller \
    --clean \
    --noconfirm \
    pyinstaller/git-adr.spec

# Check if build succeeded (onedir mode creates dist/git-adr/git-adr)
BINARY="dist/git-adr/git-adr"
if [[ -f "$BINARY" ]]; then
    # Get total distribution size
    SIZE=$(du -sh "dist/git-adr" | cut -f1)
    info "Build successful!"
    info "Binary: $BINARY"
    info "Distribution size: $SIZE"

    # Quick version check
    info "Testing binary..."
    if ./$BINARY --version; then
        info "Binary test passed!"
    else
        warn "Binary test failed - may have missing dependencies"
    fi
else
    error "Build failed - no binary produced"
fi

# Deactivate venv
deactivate

info "Build complete!"
echo ""
echo "Next steps:"
echo "  1. Run smoke tests: ./scripts/smoke-test.sh dist/git-adr/git-adr"
echo "  2. Test commands: ./dist/git-adr/git-adr --help"
