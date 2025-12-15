# git-adr Makefile
# Orchestrates testing with proper temp git repo management

.PHONY: all clean test test-unit test-integration test-coverage lint format check install dev-install help docs man-pages install-man

# Python and venv
PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
RUFF := $(VENV_BIN)/ruff

# Test directories
TEST_DIR := tests
TEST_TMP_DIR := $(TEST_DIR)/.tmp
COVERAGE_DIR := coverage

# Coverage threshold
COVERAGE_THRESHOLD := 95

# Default target
all: check test

# Help
help:
	@echo "git-adr Makefile targets:"
	@echo ""
	@echo "Development:"
	@echo "  make install        Install production dependencies"
	@echo "  make dev-install    Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests with coverage"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-coverage  Run tests with detailed coverage report"
	@echo "  make test-quick     Quick test run (no coverage)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linter (ruff check)"
	@echo "  make format         Format code (ruff format)"
	@echo "  make check          Run all quality checks"
	@echo "  make ci             Full CI checks (clean, check, test)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs           Build all documentation"
	@echo "  make man-pages      Generate man pages (requires pandoc)"
	@echo "  make install-man    Install man pages to system"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Clean temp files and caches"
	@echo ""

# Installation
install:
	$(PIP) install -e .

dev-install:
	$(PIP) install -e ".[dev,ai]"

# Create temp test directory
$(TEST_TMP_DIR):
	@mkdir -p $(TEST_TMP_DIR)

# Clean temp test repos and caches
clean:
	@echo "Cleaning temp test repos..."
	@rm -rf $(TEST_TMP_DIR)
	@rm -rf .pytest_cache
	@rm -rf $(COVERAGE_DIR)
	@rm -rf .coverage
	@rm -rf htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# Linting
lint:
	$(RUFF) check src/ tests/

# Formatting
format:
	$(RUFF) format src/ tests/

# Format check (no changes)
format-check:
	$(RUFF) format --check src/ tests/

# All quality checks
check: lint format-check
	@echo "All quality checks passed!"

# Unit tests (fast, no real git repos needed)
test-unit:
	$(PYTEST) $(TEST_DIR) -v \
		-m "not integration" \
		--tb=short

# Integration tests (require real git repos)
test-integration: $(TEST_TMP_DIR)
	@echo "Running integration tests with temp git repos..."
	GIT_ADR_TEST_TMP=$(TEST_TMP_DIR) $(PYTEST) $(TEST_DIR) -v \
		-m "integration" \
		--tb=short
	@echo "Cleaning up temp repos..."
	@rm -rf $(TEST_TMP_DIR)/*

# All tests with coverage
test: $(TEST_TMP_DIR)
	@echo "Running all tests with coverage..."
	GIT_ADR_TEST_TMP=$(TEST_TMP_DIR) $(PYTEST) $(TEST_DIR) -v \
		--cov=src/git_adr \
		--cov-report=term-missing \
		--cov-report=html:$(COVERAGE_DIR) \
		--cov-fail-under=$(COVERAGE_THRESHOLD) \
		--tb=short
	@echo "Cleaning up temp repos..."
	@rm -rf $(TEST_TMP_DIR)/*
	@echo "Coverage report available at $(COVERAGE_DIR)/index.html"

# Detailed coverage report
test-coverage: $(TEST_TMP_DIR)
	@echo "Running tests with detailed coverage..."
	GIT_ADR_TEST_TMP=$(TEST_TMP_DIR) $(PYTEST) $(TEST_DIR) -v \
		--cov=src/git_adr \
		--cov-report=term-missing \
		--cov-report=html:$(COVERAGE_DIR) \
		--cov-report=xml:$(COVERAGE_DIR)/coverage.xml \
		--tb=short
	@rm -rf $(TEST_TMP_DIR)/*
	@echo ""
	@echo "Coverage reports:"
	@echo "  HTML: $(COVERAGE_DIR)/index.html"
	@echo "  XML:  $(COVERAGE_DIR)/coverage.xml"

# Quick test (no coverage, fast feedback)
test-quick:
	$(PYTEST) $(TEST_DIR) -v --tb=short -x

# CI target (strict)
ci: clean check test
	@echo "CI checks passed!"

# ============================================================
# Documentation
# ============================================================

# Directories
DOCS_DIR := docs
MAN_DIR := $(DOCS_DIR)/man
MAN_OUT_DIR := man

# Generate man pages from markdown sources using pandoc
# Requires: pandoc (brew install pandoc / apt-get install pandoc)
man-pages:
	@echo "Generating man pages from markdown sources..."
	@mkdir -p $(MAN_OUT_DIR)/man1
	@if command -v pandoc >/dev/null 2>&1; then \
		for md in $(MAN_DIR)/*.md; do \
			name=$$(basename $$md .md); \
			echo "  Converting $$name..."; \
			pandoc -s -t man $$md -o $(MAN_OUT_DIR)/man1/$$name 2>/dev/null || true; \
		done; \
		echo "Man pages generated in $(MAN_OUT_DIR)/man1/"; \
	else \
		echo "Note: pandoc not installed. Man page sources in $(MAN_DIR)/"; \
		echo "Install pandoc to generate man format: brew install pandoc"; \
	fi

# Install man pages to system directory
# Default: /usr/local/share/man (configurable via MAN_INSTALL_DIR)
MAN_INSTALL_DIR ?= /usr/local/share/man
install-man: man-pages
	@if [ -d "$(MAN_OUT_DIR)/man1" ] && [ -n "$$(ls -A $(MAN_OUT_DIR)/man1 2>/dev/null)" ]; then \
		echo "Installing man pages to $(MAN_INSTALL_DIR)/man1/..."; \
		mkdir -p $(MAN_INSTALL_DIR)/man1; \
		cp $(MAN_OUT_DIR)/man1/* $(MAN_INSTALL_DIR)/man1/; \
		echo "Man pages installed. Try: man git-adr"; \
	else \
		echo "Error: No man pages generated. Install pandoc first: brew install pandoc"; \
		exit 1; \
	fi

# Build all documentation
docs: man-pages
	@echo ""
	@echo "Documentation available:"
	@echo "  $(MAN_DIR)/*.md         - Man page sources (markdown)"
	@echo "  $(DOCS_DIR)/COMMANDS.md - Command quick reference"
	@echo ""
	@echo "View man pages: man $(MAN_OUT_DIR)/git-adr.1"
	@echo "Or read markdown: cat $(MAN_DIR)/git-adr.1.md"
