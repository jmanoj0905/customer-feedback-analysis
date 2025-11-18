#!/bin/bash

###############################################
# Project Validation Script
# Checks all files for syntax errors
###############################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARNINGS++))
}

print_header "Validating Customer Feedback Analysis Project"

# Check Python syntax
print_header "Checking Python Files"
for file in $(find . -name "*.py" -type f | grep -v __pycache__); do
    if python3 -m py_compile "$file" 2>/dev/null; then
        print_success "Python syntax: $file"
    else
        print_error "Python syntax error: $file"
    fi
done

# Check JSON files
print_header "Checking JSON Files"
for file in $(find . -name "*.json" -type f | grep -v node_modules); do
    if python3 -m json.tool "$file" > /dev/null 2>&1; then
        print_success "JSON valid: $file"
    else
        print_error "JSON error: $file"
    fi
done

# Check JavaScript syntax
print_header "Checking JavaScript Files"
for file in $(find ./frontend/src -name "*.js" -type f 2>/dev/null); do
    if node -c "$file" 2>/dev/null; then
        print_success "JavaScript syntax: $file"
    else
        print_error "JavaScript syntax error: $file"
    fi
done

# Check shell scripts
print_header "Checking Shell Scripts"
for file in $(find . -name "*.sh" -type f); do
    if bash -n "$file" 2>/dev/null; then
        print_success "Shell script syntax: $file"
    else
        print_error "Shell script error: $file"
    fi
done

# Check required files exist
print_header "Checking Required Files"
required_files=(
    "README.md"
    "LICENSE"
    ".gitignore"
    "requirements.txt"
    "config.json"
    "backend/lambda/analyze_feedback/lambda_function.py"
    "backend/lambda/get_analytics/lambda_function.py"
    "backend/utils/comprehend_helper.py"
    "frontend/public/index.html"
    "frontend/src/js/app.js"
    "frontend/src/js/api.js"
    "frontend/src/js/charts.js"
    "frontend/src/css/style.css"
    "infrastructure/cloudformation/template.yaml"
    "infrastructure/terraform/main.tf"
    "docs/architecture.md"
    "docs/setup.md"
    "docs/api_documentation.md"
    "tests/test_lambda.py"
    "scripts/deploy.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
    fi
done

# Check directory structure
print_header "Checking Directory Structure"
required_dirs=(
    "backend/lambda/analyze_feedback"
    "backend/lambda/get_analytics"
    "backend/utils"
    "frontend/public"
    "frontend/src/js"
    "frontend/src/css"
    "infrastructure/cloudformation"
    "infrastructure/terraform"
    "docs"
    "tests"
    "scripts"
    "data"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "Directory exists: $dir"
    else
        print_error "Missing directory: $dir"
    fi
done

# Summary
print_header "Validation Summary"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo -e "${GREEN}Project is ready for deployment.${NC}"
else
    echo -e "${RED}Found $ERRORS error(s)${NC}"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Found $WARNINGS warning(s)${NC}"
fi

echo ""
echo "Next steps:"
echo "1. Review any warnings above"
echo "2. Run: ./scripts/deploy.sh to deploy to AWS"
echo "3. Run: python -m pytest tests/ to run unit tests"
