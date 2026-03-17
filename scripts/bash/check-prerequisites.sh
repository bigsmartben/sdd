#!/usr/bin/env bash

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-tasks     Require tasks.md to exist (for implementation phase)
#   --include-tasks     Include tasks.md in AVAILABLE_DOCS list
#   --task-preflight    Include compact tasks bootstrap packet extracted from plan.md (JSON mode only)
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
TASK_PREFLIGHT=false
PATHS_ONLY=false
PLAN_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            shift
            ;;
        --include-tasks)
            INCLUDE_TASKS=true
            shift
            ;;
        --task-preflight)
            TASK_PREFLIGHT=true
            shift
            ;;
        --paths-only)
            PATHS_ONLY=true
            shift
            ;;
        --plan-file)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --plan-file requires a path to plan.md" >&2
                exit 1
            fi
            PLAN_FILE="$2"
            shift 2
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --task-preflight    Include compact tasks bootstrap packet extracted from plan.md (JSON mode only)
  --plan-file <path>  Explicit path to plan.md under repo/specs/** for planning commands
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  ./check-prerequisites.sh --json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  ./check-prerequisites.sh --json --require-tasks --include-tasks

  # Resolve planning inputs from an explicit plan.md path
  ./check-prerequisites.sh --json --plan-file specs/001-demo/plan.md

  # Extract compact tasks bootstrap packet for /sdd.tasks
  ./check-prerequisites.sh --json --task-preflight
  
  # Get feature paths only (no validation)
  ./check-prerequisites.sh --paths-only
  
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$1'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths and validate branch when using active-feature discovery.
if [[ -n "$PLAN_FILE" ]]; then
    FEATURE_PATHS_ENV="$(get_feature_paths_from_plan_file "$PLAN_FILE")" || exit 1
    eval "$FEATURE_PATHS_ENV"
else
    eval "$(get_feature_paths)"
    check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1
fi

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":%s,"BRANCH":%s,"FEATURE_DIR":%s,"FEATURE_SPEC":%s,"IMPL_PLAN":%s,"TASKS":%s}\n' \
            "$(json_string "$REPO_ROOT")" \
            "$(json_string "$CURRENT_BRANCH")" \
            "$(json_string "$FEATURE_DIR")" \
            "$(json_string "$FEATURE_SPEC")" \
            "$(json_string "$IMPL_PLAN")" \
            "$(json_string "$TASKS")"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo "FEATURE_SPEC: $FEATURE_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
        echo "TASKS: $TASKS"
    fi
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /sdd.specify first to create the feature structure." >&2
    exit 1
fi

if [[ ! -f "$IMPL_PLAN" ]]; then
    echo "ERROR: plan.md not found in $FEATURE_DIR" >&2
    echo "Run /sdd.plan first to create the implementation plan." >&2
    exit 1
fi

# Check for tasks.md if required
if $REQUIRE_TASKS && [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run /sdd.tasks first to create the task list." >&2
    exit 1
fi

# Task preflight requires JSON mode because it augments the JSON payload.
if $TASK_PREFLIGHT && ! $JSON_MODE; then
    echo "ERROR: --task-preflight requires --json output mode." >&2
    exit 1
fi

# Build list of available documents
docs=()

# Check planning support docs when present
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")

# Check contracts directory (only if it exists and has files)
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi

[[ -f "$TEST_MATRIX" ]] && docs+=("test-matrix.md")

# Include tasks.md if requested and it exists
if $INCLUDE_TASKS && [[ -f "$TASKS" ]]; then
    docs+=("tasks.md")
fi

# Output results
if $JSON_MODE; then
    # Build JSON array of documents
    json_docs="$(json_array "${docs[@]}")"

    if $TASK_PREFLIGHT; then
        TASK_PREFLIGHT_SCRIPT="$SCRIPT_DIR/../task_preflight.py"
        task_bootstrap="null"
        PYTHON_BIN="$(command -v python3 || command -v python || true)"
        if [[ -f "$TASK_PREFLIGHT_SCRIPT" && -n "$PYTHON_BIN" ]]; then
            if task_bootstrap="$("$PYTHON_BIN" "$TASK_PREFLIGHT_SCRIPT" \
                --feature-dir "$FEATURE_DIR" \
                --plan "$IMPL_PLAN" \
                --spec "$FEATURE_SPEC" \
                --data-model "$DATA_MODEL" \
                --test-matrix "$TEST_MATRIX" \
                --contracts-dir "$CONTRACTS_DIR")"; then
                :
            else
                task_bootstrap="null"
            fi
        fi

        printf '{"FEATURE_DIR":%s,"AVAILABLE_DOCS":%s,"TASKS_BOOTSTRAP":%s}\n' \
            "$(json_string "$FEATURE_DIR")" \
            "$json_docs" \
            "$task_bootstrap"
    else
        printf '{"FEATURE_DIR":%s,"AVAILABLE_DOCS":%s}\n' \
            "$(json_string "$FEATURE_DIR")" \
            "$json_docs"
    fi
else
    # Text output
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    check_file "$RESEARCH" "research.md"
    check_file "$DATA_MODEL" "data-model.md"
    check_dir "$CONTRACTS_DIR" "contracts/"
    check_file "$TEST_MATRIX" "test-matrix.md"
    
    if $INCLUDE_TASKS; then
        check_file "$TASKS" "tasks.md"
    fi
fi
