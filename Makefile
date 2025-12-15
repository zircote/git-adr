# git-adr Makefile
# Orchestrates testing with proper temp git repo management

.PHONY: all clean test test-unit test-integration test-coverage lint format check install dev-install help

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
	@echo "  make install        Install production dependencies"
	@echo "  make dev-install    Install development dependencies"
	@echo "  make test           Run all tests with coverage"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-coverage  Run tests with detailed coverage report"
	@echo "  make lint           Run linter (ruff check)"
	@echo "  make format         Format code (ruff format)"
	@echo "  make check          Run all quality checks"
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
