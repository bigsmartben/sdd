#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  Uses current feature branch to resolve specs/<feature-key>/spec.md"
            echo "  --json              Output results in JSON format"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Error: Unknown option '$1'" >&2
            exit 1
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_feature_paths)"
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
if [[ ! -r "$TEMPLATE" ]]; then
    echo "Error: Required runtime template not found or not readable at $TEMPLATE" >&2
    exit 1
fi

if [[ ! -f "$FEATURE_SPEC" ]]; then
    echo "Error: spec.md not found at $FEATURE_SPEC" >&2
    exit 1
fi

CONSTITUTION="$REPO_ROOT/.specify/memory/constitution.md"
DEPENDENCY_MATRIX="$REPO_ROOT/.specify/memory/repository-first/technical-dependency-matrix.md"
MODULE_INVOCATION="$REPO_ROOT/.specify/memory/repository-first/module-invocation-spec.md"

for required_file in "$CONSTITUTION" "$DEPENDENCY_MATRIX" "$MODULE_INVOCATION"; do
    if [[ ! -r "$required_file" ]]; then
        echo "Error: Required constitution or repository-first baseline not found or not readable at $required_file. Run /sdd.constitution first." >&2
        exit 1
    fi

    if [[ ! -s "$required_file" ]]; then
        echo "Error: Required constitution or repository-first baseline is empty at $required_file. Run /sdd.constitution first." >&2
        exit 1
    fi
done

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy plan template
cp "$TEMPLATE" "$IMPL_PLAN"
if ! $JSON_MODE; then
    echo "Copied plan template to $IMPL_PLAN"
fi

# Output results
if $JSON_MODE; then
    printf '{"FEATURE_SPEC":%s,"IMPL_PLAN":%s,"SPECS_DIR":%s,"BRANCH":%s,"HAS_GIT":%s}\n' \
        "$(json_string "$FEATURE_SPEC")" \
        "$(json_string "$IMPL_PLAN")" \
        "$(json_string "$FEATURE_DIR")" \
        "$(json_string "$CURRENT_BRANCH")" \
        "$(json_string "$HAS_GIT")"
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN" 
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi
