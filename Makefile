# git-adr Makefile
# Build, test, and install git-adr (Rust implementation)

.PHONY: all clean test test-unit lint format check build build-release \
        install install-bin uninstall help ci dev docs \
        version bump-patch bump-minor bump-major tag \
        release-patch release-minor release-major \
        clippy audit deny completions

# ============================================================
# Configuration
# ============================================================

DESTDIR ?=
prefix ?= /usr/local
bindir ?= $(prefix)/bin
mandir ?= $(prefix)/share/man
datadir ?= $(prefix)/share

# Completion directories
BASH_COMPLETION_DIR ?= $(datadir)/bash-completion/completions
ZSH_COMPLETION_DIR ?= $(datadir)/zsh/site-functions
FISH_COMPLETION_DIR ?= $(datadir)/fish/vendor_completions.d

# Project paths
TARGET_DIR := target
SHARE_DIR := share
COMPLETION_DIR := $(SHARE_DIR)/completions

# Binary name
BINARY := git-adr

# Version from Cargo.toml
VERSION := $(shell grep -m1 '^version' Cargo.toml | cut -d'"' -f2)

# Features
FEATURES ?= all

# ============================================================
# Default target
# ============================================================

all: build

# ============================================================
# Help
# ============================================================

help:
	@echo "git-adr Makefile (v$(VERSION))"
	@echo ""
	@echo "Build:"
	@echo "  make build          Build debug binary"
	@echo "  make build-release  Build optimized release binary"
	@echo "  make completions    Generate shell completion scripts"
	@echo ""
	@echo "Install (may require sudo):"
	@echo "  make install        Install binary to $(bindir)"
	@echo "  make install-completions  Install shell completions"
	@echo "  make uninstall      Remove installed files"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make lint           Run clippy lints"
	@echo "  make format         Format code with rustfmt"
	@echo "  make check          Run format check + clippy"
	@echo "  make audit          Run cargo audit (security)"
	@echo "  make deny           Run cargo deny (licenses/advisories)"
	@echo "  make ci             Full CI checks (mirrors GitHub Actions)"
	@echo "  make docs           Generate documentation"
	@echo ""
	@echo "Version:"
	@echo "  make version        Show current version"
	@echo "  make bump-patch     Bump patch version (0.2.3 -> 0.2.4)"
	@echo "  make bump-minor     Bump minor version (0.2.3 -> 0.3.0)"
	@echo "  make bump-major     Bump major version (0.2.3 -> 1.0.0)"
	@echo "  make tag            Create git tag for current version"
	@echo ""
	@echo "Release:"
	@echo "  make release-patch  Bump patch, tag, ready to push"
	@echo "  make release-minor  Bump minor, tag, ready to push"
	@echo "  make release-major  Bump major, tag, ready to push"
	@echo "  make clean          Clean build artifacts"
	@echo ""
	@echo "Configuration:"
	@echo "  prefix=$(prefix)"
	@echo "  DESTDIR=$(DESTDIR)"
	@echo "  FEATURES=$(FEATURES)"

# ============================================================
# Build targets
# ============================================================

build:
	cargo build --features $(FEATURES)

build-release:
	cargo build --release --features $(FEATURES)

# Generate shell completion scripts
completions: build
	@echo "Generating shell completions..."
	@mkdir -p $(COMPLETION_DIR)
	@$(TARGET_DIR)/debug/$(BINARY) completion bash > $(COMPLETION_DIR)/git-adr.bash 2>/dev/null || \
		echo "  (bash completion generation not yet implemented)"
	@$(TARGET_DIR)/debug/$(BINARY) completion zsh > $(COMPLETION_DIR)/_git-adr 2>/dev/null || \
		echo "  (zsh completion generation not yet implemented)"
	@$(TARGET_DIR)/debug/$(BINARY) completion fish > $(COMPLETION_DIR)/git-adr.fish 2>/dev/null || \
		echo "  (fish completion generation not yet implemented)"

# ============================================================
# Installation targets
# ============================================================

install: install-bin
	@echo ""
	@echo "git-adr $(VERSION) installed successfully!"
	@echo ""
	@echo "Quick start:"
	@echo "  git adr init              # Initialize in a repository"
	@echo "  git adr new 'Title'       # Create an ADR"
	@echo "  git adr list              # List all ADRs"

install-bin: build-release
	@echo "Installing git-adr binary..."
	install -d $(DESTDIR)$(bindir)
	install -m 755 $(TARGET_DIR)/release/$(BINARY) $(DESTDIR)$(bindir)/$(BINARY)
	@echo "Installed to $(DESTDIR)$(bindir)/$(BINARY)"

install-completions: completions
	@echo "Installing shell completions..."
	@if [ -f "$(COMPLETION_DIR)/git-adr.bash" ]; then \
		install -d $(DESTDIR)$(BASH_COMPLETION_DIR); \
		install -m 644 $(COMPLETION_DIR)/git-adr.bash $(DESTDIR)$(BASH_COMPLETION_DIR)/git-adr; \
		echo "  bash: $(DESTDIR)$(BASH_COMPLETION_DIR)/git-adr"; \
	fi
	@if [ -f "$(COMPLETION_DIR)/_git-adr" ]; then \
		install -d $(DESTDIR)$(ZSH_COMPLETION_DIR); \
		install -m 644 $(COMPLETION_DIR)/_git-adr $(DESTDIR)$(ZSH_COMPLETION_DIR)/_git-adr; \
		echo "  zsh:  $(DESTDIR)$(ZSH_COMPLETION_DIR)/_git-adr"; \
	fi
	@if [ -f "$(COMPLETION_DIR)/git-adr.fish" ]; then \
		install -d $(DESTDIR)$(FISH_COMPLETION_DIR); \
		install -m 644 $(COMPLETION_DIR)/git-adr.fish $(DESTDIR)$(FISH_COMPLETION_DIR)/git-adr.fish; \
		echo "  fish: $(DESTDIR)$(FISH_COMPLETION_DIR)/git-adr.fish"; \
	fi

uninstall:
	@echo "Uninstalling git-adr..."
	rm -f $(DESTDIR)$(bindir)/$(BINARY)
	rm -f $(DESTDIR)$(BASH_COMPLETION_DIR)/git-adr
	rm -f $(DESTDIR)$(ZSH_COMPLETION_DIR)/_git-adr
	rm -f $(DESTDIR)$(FISH_COMPLETION_DIR)/git-adr.fish
	@echo "Uninstall complete."

# ============================================================
# Testing targets
# ============================================================

test:
	cargo test --all-features

test-unit:
	cargo test --all-features --lib

# ============================================================
# Code quality targets
# ============================================================

lint: clippy

clippy:
	cargo clippy --all-targets --all-features -- -D warnings

format:
	cargo fmt

format-check:
	cargo fmt -- --check

check: format-check clippy
	@echo "All quality checks passed!"

audit:
	@if command -v cargo-audit >/dev/null 2>&1; then \
		cargo audit; \
	else \
		echo "cargo-audit not installed. Install with: cargo install cargo-audit"; \
	fi

deny:
	@if command -v cargo-deny >/dev/null 2>&1; then \
		cargo deny check; \
	else \
		echo "cargo-deny not installed. Install with: cargo install cargo-deny"; \
	fi

# Full CI check (mirrors GitHub Actions)
ci: check test
	@echo "CI checks passed!"

# ============================================================
# Documentation
# ============================================================

docs:
	cargo doc --all-features --open

# ============================================================
# Version management
# ============================================================

version:
	@echo "$(VERSION)"

# Bump patch version (0.2.3 -> 0.2.4)
bump-patch:
	@current=$(VERSION) && \
	major=$$(echo $$current | cut -d. -f1) && \
	minor=$$(echo $$current | cut -d. -f2) && \
	patch=$$(echo $$current | cut -d. -f3) && \
	new_patch=$$((patch + 1)) && \
	new_version="$$major.$$minor.$$new_patch" && \
	sed -i.bak "s/^version = \"$$current\"/version = \"$$new_version\"/" Cargo.toml && \
	rm -f Cargo.toml.bak && \
	echo "Bumped version: $$current -> $$new_version"

# Bump minor version (0.2.3 -> 0.3.0)
bump-minor:
	@current=$(VERSION) && \
	major=$$(echo $$current | cut -d. -f1) && \
	minor=$$(echo $$current | cut -d. -f2) && \
	new_minor=$$((minor + 1)) && \
	new_version="$$major.$$new_minor.0" && \
	sed -i.bak "s/^version = \"$$current\"/version = \"$$new_version\"/" Cargo.toml && \
	rm -f Cargo.toml.bak && \
	echo "Bumped version: $$current -> $$new_version"

# Bump major version (0.2.3 -> 1.0.0)
bump-major:
	@current=$(VERSION) && \
	major=$$(echo $$current | cut -d. -f1) && \
	new_major=$$((major + 1)) && \
	new_version="$$new_major.0.0" && \
	sed -i.bak "s/^version = \"$$current\"/version = \"$$new_version\"/" Cargo.toml && \
	rm -f Cargo.toml.bak && \
	echo "Bumped version: $$current -> $$new_version"

# Create git tag for current version
tag:
	git tag -a "v$(VERSION)" -m "Release v$(VERSION)"
	@echo "Created tag: v$(VERSION)"

# Bump and tag shortcuts
release-patch: bump-patch tag
	@echo "Release ready. Run 'git push --follow-tags' to publish."

release-minor: bump-minor tag
	@echo "Release ready. Run 'git push --follow-tags' to publish."

release-major: bump-major tag
	@echo "Release ready. Run 'git push --follow-tags' to publish."

# ============================================================
# Clean target
# ============================================================

clean:
	@echo "Cleaning build artifacts..."
	cargo clean
	rm -rf $(SHARE_DIR)
	@echo "Clean complete."
