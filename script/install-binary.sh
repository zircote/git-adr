#!/usr/bin/env bash
# git-adr binary installer
#
# Downloads and installs pre-built git-adr binary from GitHub releases.
# No Python required!
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/zircote/git-adr/main/script/install-binary.sh | bash
#   curl -sSL https://raw.githubusercontent.com/zircote/git-adr/main/script/install-binary.sh | bash -s -- --local
#   curl -sSL https://raw.githubusercontent.com/zircote/git-adr/main/script/install-binary.sh | bash -s -- v0.1.0
#
# Options:
#   --local       Install to ~/.local/bin (no sudo required)
#   --system      Install to /usr/local/bin (default, may need sudo)
#   --verify      Verify SHA256 checksum (default: enabled)
#   --no-verify   Skip checksum verification
#   VERSION       Specific version to install (e.g., v0.1.0)
#
# Environment:
#   INSTALL_DIR   Override installation directory

set -euo pipefail

REPO="zircote/git-adr"
BINARY_NAME="git-adr"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
VERSION=""
VERIFY_CHECKSUM=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}==>${NC} $1"; }
warn() { echo -e "${YELLOW}Warning:${NC} $1"; }
error() { echo -e "${RED}Error:${NC} $1" >&2; exit 1; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --local)
            INSTALL_DIR="$HOME/.local/bin"
            shift
            ;;
        --system)
            INSTALL_DIR="/usr/local/bin"
            shift
            ;;
        --verify)
            VERIFY_CHECKSUM=true
            shift
            ;;
        --no-verify)
            VERIFY_CHECKSUM=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [VERSION]"
            echo ""
            echo "Options:"
            echo "  --local       Install to ~/.local/bin"
            echo "  --system      Install to /usr/local/bin (default)"
            echo "  --verify      Verify SHA256 checksum (default)"
            echo "  --no-verify   Skip checksum verification"
            echo "  --help        Show this help"
            echo ""
            echo "Arguments:"
            echo "  VERSION       Version to install (e.g., v0.1.0)"
            echo "                Default: latest release"
            echo ""
            echo "Examples:"
            echo "  $0                          # Install latest to /usr/local/bin"
            echo "  $0 --local                  # Install latest to ~/.local/bin"
            echo "  $0 v0.1.0                   # Install specific version"
            echo "  $0 --local --no-verify      # Install without checksum verification"
            exit 0
            ;;
        v*)
            VERSION="$1"
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Detect platform
detect_platform() {
    local os arch

    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os" in
        Darwin)
            case "$arch" in
                arm64|aarch64)
                    echo "macos-arm64"
                    ;;
                x86_64)
                    echo "macos-x86_64"
                    ;;
                *)
                    error "Unsupported architecture: $arch"
                    ;;
            esac
            ;;
        Linux)
            case "$arch" in
                x86_64)
                    echo "linux-x86_64"
                    ;;
                aarch64|arm64)
                    error "Linux ARM64 binaries not yet available. Use pip: pip install git-adr"
                    ;;
                *)
                    error "Unsupported architecture: $arch"
                    ;;
            esac
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows-x86_64"
            ;;
        *)
            error "Unsupported operating system: $os"
            ;;
    esac
}

# Get latest version from GitHub API
get_latest_version() {
    local latest
    latest=$(curl -sSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
    if [[ -z "$latest" ]]; then
        error "Failed to fetch latest version from GitHub"
    fi
    echo "$latest"
}

# Download file with progress
download() {
    local url="$1"
    local output="$2"

    if command -v curl &>/dev/null; then
        curl -sSL --progress-bar -o "$output" "$url"
    elif command -v wget &>/dev/null; then
        wget -q --show-progress -O "$output" "$url"
    else
        error "Neither curl nor wget found. Please install one of them."
    fi
}

# Verify SHA256 checksum
verify_checksum() {
    local file="$1"
    local checksum_url="$2"
    local expected actual

    info "Verifying checksum..."

    # Download checksum file
    expected=$(curl -sSL "$checksum_url" | awk '{print $1}')
    if [[ -z "$expected" ]]; then
        warn "Could not fetch checksum. Skipping verification."
        return 0
    fi

    # Calculate actual checksum
    if command -v sha256sum &>/dev/null; then
        actual=$(sha256sum "$file" | awk '{print $1}')
    elif command -v shasum &>/dev/null; then
        actual=$(shasum -a 256 "$file" | awk '{print $1}')
    else
        warn "No SHA256 tool found. Skipping verification."
        return 0
    fi

    if [[ "$expected" != "$actual" ]]; then
        error "Checksum mismatch!\n  Expected: $expected\n  Actual:   $actual"
    fi

    echo "    Checksum verified: $actual"
}

main() {
    info "Installing git-adr..."

    # Detect platform
    local platform
    platform=$(detect_platform)
    info "Detected platform: $platform"

    # Get version
    if [[ -z "$VERSION" ]]; then
        info "Fetching latest version..."
        VERSION=$(get_latest_version)
    fi
    info "Version: $VERSION"

    # Construct URLs
    local base_url="https://github.com/${REPO}/releases/download/${VERSION}"
    local artifact_name="git-adr-${platform}"
    local archive_url archive_ext checksum_url

    if [[ "$platform" == "windows-x86_64" ]]; then
        archive_ext="zip"
    else
        archive_ext="tar.gz"
    fi

    archive_url="${base_url}/${artifact_name}.${archive_ext}"
    checksum_url="${archive_url}.sha256"

    # Create temp directory
    local tmpdir
    tmpdir=$(mktemp -d)
    trap 'rm -rf "$tmpdir"' EXIT

    # Download archive
    local archive_file="${tmpdir}/${artifact_name}.${archive_ext}"
    info "Downloading ${artifact_name}.${archive_ext}..."
    download "$archive_url" "$archive_file"

    # Verify checksum
    if [[ "$VERIFY_CHECKSUM" == "true" ]]; then
        verify_checksum "$archive_file" "$checksum_url"
    fi

    # Extract archive
    info "Extracting..."
    cd "$tmpdir"
    if [[ "$archive_ext" == "zip" ]]; then
        unzip -q "$archive_file"
    else
        tar -xzf "$archive_file"
    fi

    # Find the binary
    local binary_path
    binary_path=$(find "$tmpdir" -name "$BINARY_NAME" -type f | head -1)
    if [[ -z "$binary_path" ]]; then
        # Try with .exe for Windows
        binary_path=$(find "$tmpdir" -name "${BINARY_NAME}.exe" -type f | head -1)
    fi

    if [[ -z "$binary_path" ]]; then
        error "Binary not found in archive"
    fi

    # Create install directory if needed
    if [[ ! -d "$INSTALL_DIR" ]]; then
        info "Creating $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR"
    fi

    # Install binary
    info "Installing to $INSTALL_DIR..."
    chmod +x "$binary_path"

    # Use sudo if needed
    if [[ -w "$INSTALL_DIR" ]]; then
        cp "$binary_path" "$INSTALL_DIR/"
        # For onedir mode, also copy the _internal directory
        local internal_dir="${tmpdir}/${artifact_name}/_internal"
        if [[ -d "$internal_dir" ]]; then
            mkdir -p "$INSTALL_DIR/_internal"
            cp -r "$internal_dir/"* "$INSTALL_DIR/_internal/"
        fi
    else
        sudo cp "$binary_path" "$INSTALL_DIR/"
        local internal_dir="${tmpdir}/${artifact_name}/_internal"
        if [[ -d "$internal_dir" ]]; then
            sudo mkdir -p "$INSTALL_DIR/_internal"
            sudo cp -r "$internal_dir/"* "$INSTALL_DIR/_internal/"
        fi
    fi

    # Set up git alias
    info "Setting up git alias..."
    git config --global alias.adr '!git-adr' 2>/dev/null || true

    # Verify installation
    if command -v git-adr &>/dev/null; then
        echo ""
        echo -e "${GREEN}git-adr installed successfully!${NC}"
        git-adr --version
        echo ""
        echo "Quick start:"
        echo "  git adr init              # Initialize in a repository"
        echo "  git adr new 'Title'       # Create an ADR"
        echo "  git adr list              # List all ADRs"
    else
        echo ""
        echo -e "${YELLOW}Note:${NC} git-adr installed but may not be in PATH."
        echo "Add to your shell config:"
        echo "  export PATH=\"\$PATH:$INSTALL_DIR\""
    fi
}

main "$@"
