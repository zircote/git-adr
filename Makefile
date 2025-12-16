# git-adr Makefile
# Build, test, and install git-adr following git extension conventions

.PHONY: all clean test test-unit test-integration test-coverage lint format check \
        build man-pages completions install install-bin install-man install-completions \
        uninstall dist release help ci dev-install docs typecheck security audit \
        binary binary-clean smoke-test

# ============================================================
# Configuration (following gh CLI conventions)
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
VENV := .venv
VENV_BIN := $(VENV)/bin
DIST_DIR := dist
BUILD_DIR := build
SHARE_DIR := share
MAN_SRC_DIR := docs/man
MAN_OUT_DIR := $(SHARE_DIR)/man/man1
COMPLETION_DIR := $(SHARE_DIR)/completions

# Test directories
TEST_DIR := tests
TEST_TMP_DIR := $(TEST_DIR)/.tmp
COVERAGE_DIR := coverage
COVERAGE_THRESHOLD := 95

# Version from pyproject.toml
VERSION := $(shell grep -m1 'version' pyproject.toml | cut -d'"' -f2)

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
	@echo "  make build          Build package and all artifacts"
	@echo "  make man-pages      Generate man pages (requires pandoc)"
	@echo "  make completions    Generate shell completion scripts"
	@echo "  make dist           Build distribution packages"
	@echo ""
	@echo "Install (may require sudo):"
	@echo "  make install        Install everything (bin, man, completions)"
	@echo "  make install-bin    Install binary only"
	@echo "  make install-man    Install man pages only"
	@echo "  make install-completions  Install shell completions only"
	@echo "  make uninstall      Remove installed files"
	@echo ""
	@echo "Development:"
	@echo "  make dev-install    Install in development mode"
	@echo "  make test           Run all tests with coverage"
	@echo "  make test-quick     Quick test run (no coverage)"
	@echo "  make lint           Run linter"
	@echo "  make format         Format code"
	@echo "  make typecheck      Run mypy type checking"
	@echo "  make security       Run bandit security scan"
	@echo "  make audit          Run pip-audit dependency check"
	@echo "  make check          Run lint + format check"
	@echo "  make ci             Full CI checks (mirrors GitHub Actions)"
	@echo ""
	@echo "Binary (standalone executable):"
	@echo "  make binary         Build standalone binary with PyInstaller"
	@echo "  make binary-clean   Clean and rebuild binary"
	@echo "  make smoke-test     Run smoke tests against binary"
	@echo ""
	@echo "Release:"
	@echo "  make release        Build release tarball with all artifacts"
	@echo "  make clean          Clean build artifacts"
	@echo ""
	@echo "Configuration:"
	@echo "  prefix=$(prefix)"
	@echo "  DESTDIR=$(DESTDIR)"

# ============================================================
# Build targets
# ============================================================

build: man-pages completions
	@echo "Build complete. Run 'make install' to install."

# Generate man pages from markdown (requires pandoc)
man-pages:
	@echo "Generating man pages..."
	@mkdir -p $(MAN_OUT_DIR)
	@if command -v pandoc >/dev/null 2>&1; then \
		for md in $(MAN_SRC_DIR)/*.md; do \
			name=$$(basename $$md .md); \
			echo "  $$name"; \
			pandoc -s -t man $$md -o $(MAN_OUT_DIR)/$$name 2>/dev/null || true; \
		done; \
	else \
		echo "Warning: pandoc not installed, skipping man page generation"; \
		echo "Install with: brew install pandoc"; \
	fi

# Generate shell completion scripts
completions:
	@echo "Generating shell completions..."
	@mkdir -p $(COMPLETION_DIR)
	@if [ -x "$(VENV_BIN)/git-adr" ]; then \
		$(VENV_BIN)/git-adr completion bash > $(COMPLETION_DIR)/git-adr.bash 2>/dev/null || true; \
		$(VENV_BIN)/git-adr completion zsh > $(COMPLETION_DIR)/_git-adr 2>/dev/null || true; \
		$(VENV_BIN)/git-adr completion fish > $(COMPLETION_DIR)/git-adr.fish 2>/dev/null || true; \
		echo "  bash: $(COMPLETION_DIR)/git-adr.bash"; \
		echo "  zsh:  $(COMPLETION_DIR)/_git-adr"; \
		echo "  fish: $(COMPLETION_DIR)/git-adr.fish"; \
	else \
		echo "Warning: git-adr not installed in venv, run 'make dev-install' first"; \
	fi

# Build distribution packages
dist: build
	@echo "Building distribution packages..."
	uv build
	@echo "Distribution packages in $(DIST_DIR)/"

# ============================================================
# Installation targets (following gh CLI conventions)
# ============================================================

install: install-bin install-man install-completions
	@echo ""
	@echo "git-adr $(VERSION) installed successfully!"
	@echo ""
	@echo "Quick start:"
	@echo "  git adr init              # Initialize in a repository"
	@echo "  git adr new 'Title'       # Create an ADR"
	@echo "  git adr list              # List all ADRs"
	@echo ""
	@echo "Enable completion (if not auto-loaded):"
	@echo "  source $(DESTDIR)$(BASH_COMPLETION_DIR)/git-adr"

install-bin:
	@echo "Installing git-adr binary..."
	@if [ -x "$(VENV_BIN)/git-adr" ]; then \
		install -d $(DESTDIR)$(bindir); \
		install -m 755 $(VENV_BIN)/git-adr $(DESTDIR)$(bindir)/git-adr; \
		echo "Installed to $(DESTDIR)$(bindir)/git-adr"; \
	else \
		echo "Error: git-adr not found in venv. Run 'make dev-install' first."; \
		echo ""; \
		echo "Alternative: Install directly with:"; \
		echo "  uv tool install git-adr"; \
		echo "  # or: pipx install git-adr"; \
		exit 1; \
	fi

install-man: man-pages
	@echo "Installing man pages..."
	@if [ -d "$(MAN_OUT_DIR)" ] && [ -n "$$(ls -A $(MAN_OUT_DIR) 2>/dev/null)" ]; then \
		install -d $(DESTDIR)$(mandir)/man1; \
		install -m 644 $(MAN_OUT_DIR)/* $(DESTDIR)$(mandir)/man1/; \
		echo "Installed to $(DESTDIR)$(mandir)/man1/"; \
	else \
		echo "No man pages found. Run 'make man-pages' first (requires pandoc)."; \
	fi

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
	rm -f $(DESTDIR)$(bindir)/git-adr
	rm -f $(DESTDIR)$(mandir)/man1/git-adr*.1
	rm -f $(DESTDIR)$(BASH_COMPLETION_DIR)/git-adr
	rm -f $(DESTDIR)$(ZSH_COMPLETION_DIR)/_git-adr
	rm -f $(DESTDIR)$(FISH_COMPLETION_DIR)/git-adr.fish
	@echo "Uninstall complete."

# ============================================================
# Release target (creates tarball with all artifacts)
# ============================================================

RELEASE_NAME := git-adr-$(VERSION)
RELEASE_DIR := $(BUILD_DIR)/$(RELEASE_NAME)

release: build
	@echo "Building release tarball..."
	@rm -rf $(RELEASE_DIR)
	@mkdir -p $(RELEASE_DIR)
	# Copy artifacts
	cp -r $(SHARE_DIR)/* $(RELEASE_DIR)/ 2>/dev/null || true
	cp README.md $(RELEASE_DIR)/
	cp LICENSE $(RELEASE_DIR)/ 2>/dev/null || true
	cp script/install.sh $(RELEASE_DIR)/ 2>/dev/null || true
	# Create tarball
	@mkdir -p $(DIST_DIR)
	tar -czf $(DIST_DIR)/$(RELEASE_NAME).tar.gz -C $(BUILD_DIR) $(RELEASE_NAME)
	@echo "Created $(DIST_DIR)/$(RELEASE_NAME).tar.gz"

# ============================================================
# Binary targets (standalone executable with PyInstaller)
# ============================================================

BINARY_DIR := dist/git-adr
BINARY := $(BINARY_DIR)/git-adr

binary:
	@echo "Building standalone binary with PyInstaller..."
	@chmod +x scripts/build-binary.sh
	./scripts/build-binary.sh
	@echo ""
	@echo "Binary built: $(BINARY)"
	@echo "Run 'make smoke-test' to verify."

binary-clean:
	@echo "Cleaning and rebuilding binary..."
	@chmod +x scripts/build-binary.sh
	./scripts/build-binary.sh --clean

smoke-test:
	@if [ ! -f "$(BINARY)" ]; then \
		echo "Error: Binary not found at $(BINARY)"; \
		echo "Run 'make binary' first."; \
		exit 1; \
	fi
	@echo "Running smoke tests..."
	@chmod +x scripts/smoke-test.sh
	./scripts/smoke-test.sh $(BINARY)

# ============================================================
# Development targets
# ============================================================

dev-install:
	uv sync --all-extras
	@echo "Development environment ready."

# ============================================================
# Testing targets
# ============================================================

$(TEST_TMP_DIR):
	@mkdir -p $(TEST_TMP_DIR)

test: $(TEST_TMP_DIR)
	@echo "Running all tests with coverage..."
	GIT_ADR_TEST_TMP=$(TEST_TMP_DIR) uv run pytest $(TEST_DIR) -v \
		--cov=src/git_adr \
		--cov-report=term-missing \
		--cov-report=html:$(COVERAGE_DIR) \
		--cov-fail-under=$(COVERAGE_THRESHOLD) \
		--tb=short
	@rm -rf $(TEST_TMP_DIR)/*

test-unit:
	uv run pytest $(TEST_DIR) -v -m "not integration" --tb=short

test-integration: $(TEST_TMP_DIR)
	GIT_ADR_TEST_TMP=$(TEST_TMP_DIR) uv run pytest $(TEST_DIR) -v -m "integration" --tb=short
	@rm -rf $(TEST_TMP_DIR)/*

test-coverage: $(TEST_TMP_DIR)
	GIT_ADR_TEST_TMP=$(TEST_TMP_DIR) uv run pytest $(TEST_DIR) -v \
		--cov=src/git_adr \
		--cov-report=term-missing \
		--cov-report=html:$(COVERAGE_DIR) \
		--cov-report=xml:$(COVERAGE_DIR)/coverage.xml \
		--tb=short
	@rm -rf $(TEST_TMP_DIR)/*

test-quick:
	uv run pytest $(TEST_DIR) -v --tb=short -x

# ============================================================
# Code quality targets
# ============================================================

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

check: lint format-check
	@echo "All quality checks passed!"

typecheck:
	uv run mypy .

security:
	uv run bandit -r src/

audit:
	uv run pip-audit

ci: clean check typecheck security audit test
	@echo "CI checks passed!"

# ============================================================
# Clean target
# ============================================================

clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf $(SHARE_DIR)
	rm -rf $(TEST_TMP_DIR)
	rm -rf $(COVERAGE_DIR)
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf man/
	rm -rf .venv-build
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# ============================================================
# Documentation (alias for man-pages)
# ============================================================

docs: man-pages completions
	@echo ""
	@echo "Documentation built:"
	@echo "  Man pages:   $(MAN_OUT_DIR)/"
	@echo "  Completions: $(COMPLETION_DIR)/"
