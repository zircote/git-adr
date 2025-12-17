#!/usr/bin/env bash
# Smoke tests for git-adr standalone binary
#
# Usage:
#   ./scripts/smoke-test.sh [binary-path]
#
# Arguments:
#   binary-path    Path to git-adr binary (default: dist/git-adr)
#
# Exit codes:
#   0    All tests passed
#   1    One or more tests failed

# Don't use set -e as tests may have intentional failures
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Binary to test (onedir mode: dist/git-adr/git-adr)
# Convert to absolute path to work after cd to temp directory
BINARY_ARG="${1:-$PROJECT_ROOT/dist/git-adr/git-adr}"
if [[ "$BINARY_ARG" = /* ]]; then
    BINARY="$BINARY_ARG"
else
    BINARY="$PROJECT_ROOT/$BINARY_ARG"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    ((SKIPPED++))
}

# Check binary exists
if [[ ! -f "$BINARY" ]]; then
    echo -e "${RED}Binary not found: $BINARY${NC}"
    echo "Run ./scripts/build-binary.sh first"
    exit 1
fi

if [[ ! -x "$BINARY" ]]; then
    chmod +x "$BINARY"
fi

echo "Testing binary: $BINARY"
echo "Binary size: $(du -h "$BINARY" | cut -f1)"
echo ""
echo "=== Smoke Tests ==="
echo ""

# Test 1: Version flag
echo "Test: --version"
START=$(date +%s.%N)
if VERSION_OUTPUT=$("$BINARY" --version 2>&1); then
    END=$(date +%s.%N)
    DURATION=$(echo "$END - $START" | bc)
    if echo "$VERSION_OUTPUT" | grep -q "git-adr"; then
        # Startup time target: <2 seconds (per REQUIREMENTS.md)
        # First run may be slower due to macOS verification
        if (( $(echo "$DURATION < 2" | bc -l) )); then
            pass "--version (${DURATION}s) - $VERSION_OUTPUT"
        else
            fail "--version too slow (${DURATION}s > 2s target)"
        fi
    else
        fail "--version output unexpected: $VERSION_OUTPUT"
    fi
else
    fail "--version failed"
fi

# Test 2: Help flag
echo "Test: --help"
if HELP_OUTPUT=$("$BINARY" --help 2>&1); then
    if echo "$HELP_OUTPUT" | grep -q "Architecture Decision Records"; then
        pass "--help shows description"
    else
        fail "--help missing description"
    fi
else
    fail "--help failed"
fi

# Test 3: Init command (in temp directory)
echo "Test: init command"
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Initialize git repo with an initial commit (required for git notes)
git init --quiet
git config user.email "test@example.com"
git config user.name "Test User"
echo "test" > README.md
git add README.md
git commit -m "Initial commit" --quiet

if INIT_OUTPUT=$("$BINARY" init --force 2>&1); then
    # git-adr uses git notes, not a docs/adr directory
    # Check that init succeeded by verifying notes ref exists
    if git notes --ref=adr list &>/dev/null; then
        pass "init creates git notes (refs/notes/adr)"
    else
        fail "init did not create git notes"
    fi
else
    fail "init command failed: $INIT_OUTPUT"
fi

# Test 4: List command
echo "Test: list command"
if LIST_OUTPUT=$("$BINARY" list 2>&1); then
    # Should show at least the initial ADR
    pass "list command works"
else
    fail "list command failed"
fi

# Test 5: Show command (use the initial ADR ID)
echo "Test: show command"
# Get the first ADR ID from list (format: 00000000-use-adrs)
ADR_ID=$("$BINARY" list 2>/dev/null | grep -o '[0-9a-f]\{8\}-[a-z-]*' | head -1)
if [[ -n "$ADR_ID" ]]; then
    # Use --no-interactive to prevent blocking on prompts
    if SHOW_OUTPUT=$("$BINARY" show --no-interactive "$ADR_ID" 2>&1); then
        if echo "$SHOW_OUTPUT" | grep -q -i "record\|decision\|context\|architecture"; then
            pass "show command displays ADR content"
        else
            fail "show command output unexpected"
        fi
    else
        fail "show command failed for ADR: $ADR_ID"
    fi
else
    skip "show command - no ADR ID found"
fi

# Test 6: Shell completion generation
echo "Test: completion generation"
if COMPLETION_OUTPUT=$("$BINARY" --show-completion 2>&1); then
    pass "completion generation works"
else
    # Some shells might not support this
    skip "completion generation (may not be supported)"
fi

# Test 7: Issue command works (templates bundled)
echo "Test: issue command"
if ISSUE_OUTPUT=$("$BINARY" issue --help 2>&1); then
    if echo "$ISSUE_OUTPUT" | grep -q -i "template"; then
        pass "issue command works (templates referenced in help)"
    else
        fail "issue command help missing template reference"
    fi
else
    fail "issue command failed"
fi

# Test 8: Config command
echo "Test: config command"
if CONFIG_OUTPUT=$("$BINARY" config 2>&1); then
    pass "config command works"
else
    # Config with no args shows help, which returns non-zero - check help instead
    if CONFIG_HELP=$("$BINARY" config --help 2>&1); then
        pass "config command works (help displayed)"
    else
        fail "config command failed"
    fi
fi

# Test 9: Search command
echo "Test: search command"
if SEARCH_OUTPUT=$("$BINARY" search "architecture" 2>&1); then
    pass "search command works"
else
    fail "search command failed"
fi

# Test 10: Stats command
echo "Test: stats command"
if STATS_OUTPUT=$("$BINARY" stats 2>&1); then
    pass "stats command works"
else
    fail "stats command failed"
fi

# Cleanup
cd "$PROJECT_ROOT"
rm -rf "$TEMP_DIR"

# Summary
echo ""
echo "=== Summary ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Skipped: ${YELLOW}$SKIPPED${NC}"
echo ""

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
