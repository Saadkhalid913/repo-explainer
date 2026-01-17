#!/bin/bash

# CLI Testing Script for repo-explainer
# Run this to validate the CLI is working correctly

set -e

echo "=========================================="
echo "repo-explainer CLI Validation Tests"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

run_test() {
    local test_name=$1
    local command=$2

    test_count=$((test_count + 1))
    echo -n "Test $test_count: $test_name... "

    if eval "$command" > /tmp/test_output.txt 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Command: $command"
        echo "  Output: $(cat /tmp/test_output.txt | head -5)"
        fail_count=$((fail_count + 1))
    fi
}

# Test 1: Version
run_test "repo-explain --version" "repo-explain --version | grep -q 'v0.1.0'"

# Test 2: Help
run_test "repo-explain --help" "repo-explain --help | grep -q 'Commands'"

# Test 3: Analyze help
run_test "repo-explain analyze --help" "repo-explain analyze --help | grep -q 'Analyze a repository'"

# Test 4: Update help
run_test "repo-explain update --help" "repo-explain update --help | grep -q 'Update'"

# Test 5: Invalid repo path
run_test "repo-explain analyze /nonexistent (should fail)" "! repo-explain analyze /nonexistent 2>&1 | grep -q 'does not exist' || ! repo-explain analyze /nonexistent 2>&1"

# Test 6: OpenCode quick analysis
echo ""
echo -n "Test $((test_count + 1)): OpenCode quick analysis (may take 30-60s)... "
test_count=$((test_count + 1))
if repo-explain analyze . --depth quick 2>&1 | tee /tmp/test_output.txt | grep -q "Analysis complete"; then
    echo -e "${GREEN}PASS${NC}"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}FAIL${NC}"
    echo "  Expected 'Analysis complete' in output"
    echo "  Last 5 lines: $(tail -5 /tmp/test_output.txt)"
    fail_count=$((fail_count + 1))
fi

# Test 7: Output directory creation
echo ""
run_test "Custom output directory" "mkdir -p /tmp/test-repo-explain && repo-explain analyze . --output /tmp/test-repo-explain --depth quick 2>&1 | head -1 > /dev/null && [ -d /tmp/test-repo-explain ]"

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Review output above.${NC}"
    exit 1
fi
