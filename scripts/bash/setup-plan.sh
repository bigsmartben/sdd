#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
SPEC_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --spec-file)
            if [[ $# -lt 2 ]]; then
                echo "Error: --spec-file requires a path to spec.md" >&2
                exit 1
            fi
            SPEC_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 --spec-file <path/to/spec.md> [--json]"
            echo "  --spec-file <path>  Explicit path to spec.md under repo/specs/**"
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

if [[ -z "$SPEC_FILE" ]]; then
    echo "Error: --spec-file is required and must point to spec.md under repo/specs/**" >&2
    exit 1
fi

# Get all paths and variables from explicit spec file
FEATURE_PATHS_ENV="$(get_feature_paths_from_spec_file "$SPEC_FILE")" || exit 1
eval "$FEATURE_PATHS_ENV"

TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
if [[ ! -r "$TEMPLATE" ]]; then
    echo "Error: Required runtime template not found or not readable at $TEMPLATE" >&2
    exit 1
fi

if [[ ! -f "$FEATURE_SPEC" ]]; then
    echo "Error: spec.md not found at $FEATURE_SPEC" >&2
    exit 1
fi

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
