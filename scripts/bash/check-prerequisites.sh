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
#   --data-model-preflight Include compact data-model bootstrap packet extracted from plan.md (primary /sdd.plan.data-model readiness gate, JSON mode only)
#   --task-preflight    Include compact tasks bootstrap packet extracted from plan.md (primary /sdd.tasks readiness gate, JSON mode only)
#   --implement-preflight Include compact implement bootstrap packet extracted from analyze-history.md (primary /sdd.implement analyze gate, JSON mode only)
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."], ...optional bootstrap packets...}
#   Text mode: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
TASK_PREFLIGHT=false
IMPLEMENT_PREFLIGHT=false
DATA_MODEL_PREFLIGHT=false
PATHS_ONLY=false

resolve_specify_cmd() {
    local repo_shim="$SCRIPT_DIR/../../.test-bin/specify"
    if [[ -x "$repo_shim" ]]; then
        printf '%s' "$repo_shim"
        return 0
    fi
    if [[ -n "${SDD_SPECIFY_CMD:-}" ]]; then
        printf '%s' "$SDD_SPECIFY_CMD"
        return 0
    fi
    if command -v specify >/dev/null 2>&1; then
        printf 'specify'
        return 0
    fi
    if command -v specify.exe >/dev/null 2>&1; then
        printf 'specify.exe'
        return 0
    fi
    return 1
}

build_local_execution_protocol_json() {
    local search_available=false
    local search_tool="unavailable"
    local list_files_cmd=""
    local search_text_cmd=""
    if command -v rg >/dev/null 2>&1; then
        search_available=true
        search_tool="rg"
        list_files_cmd="rg --files"
        search_text_cmd="rg -n --hidden --glob '!.git/*' -- <pattern>"
    elif [[ "$HAS_GIT" == "true" ]] && command -v git >/dev/null 2>&1; then
        search_available=true
        search_tool="git"
        list_files_cmd="git ls-files"
        search_text_cmd="git grep -n -- <pattern>"
    fi

    local inspection_available=false
    local status_cmd=""
    local diff_cmd=""
    local history_cmd=""
    if [[ "$HAS_GIT" == "true" ]] && command -v git >/dev/null 2>&1; then
        inspection_available=true
        status_cmd="git status --short"
        diff_cmd="git diff -- <path>"
        history_cmd="git log --oneline -- <path>"
    fi

    local python_available=false
    local python_tool="unavailable"
    local python_runner_cmd=""
    local specify_cmd=""
    local runtime_tools="null"
    if specify_cmd="$(resolve_specify_cmd)"; then
        if runtime_tools="$("$specify_cmd" internal-runtime-tools 2>/dev/null)"; then
            python_available=true
            python_tool="specify-cli"
            python_runner_cmd="specify internal-run-python --script <helper-script> -- <helper-args>"
        else
            runtime_tools="null"
        fi
    fi

    local rules_json
    rules_json="$(json_array \
        "Reuse the emitted commands before trying alternates." \
        "Do not install missing tools or mutate PATH during /sdd runs." \
        "Use project-specific build/test commands only when they are task anchors or repo-backed scripts/configs." \
    )"

    printf '{'
    printf '"schema_version":"1.0",'
    printf '"rules":%s,' "$rules_json"
    printf '"repo_search":{"available":%s,"tool":%s,"list_files_cmd":%s,"search_text_cmd":%s},' \
        "$search_available" \
        "$(json_string "$search_tool")" \
        "$(json_string "$list_files_cmd")" \
        "$(json_string "$search_text_cmd")"
    printf '"repo_inspection":{"available":%s,"status_cmd":%s,"diff_cmd":%s,"history_cmd":%s},' \
        "$inspection_available" \
        "$(json_string "$status_cmd")" \
        "$(json_string "$diff_cmd")" \
        "$(json_string "$history_cmd")"
    printf '"python":{"available":%s,"tool":%s,"runner_cmd":%s},' \
        "$python_available" \
        "$(json_string "$python_tool")" \
        "$(json_string "$python_runner_cmd")"
    printf '"runtime_tools":%s' "$runtime_tools"
    printf '}'
}

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
        --data-model-preflight)
            DATA_MODEL_PREFLIGHT=true
            shift
            ;;
        --implement-preflight)
            IMPLEMENT_PREFLIGHT=true
            shift
            ;;
        --paths-only)
            PATHS_ONLY=true
            shift
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --data-model-preflight Include compact data-model bootstrap packet extracted from plan.md (primary /sdd.plan.data-model readiness gate, JSON mode only)
  --task-preflight    Include compact tasks bootstrap packet extracted from plan.md (primary /sdd.tasks readiness gate, JSON mode only)
  --implement-preflight Include compact implement bootstrap packet extracted from analyze-history.md (primary /sdd.implement analyze gate, JSON mode only)
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  ./check-prerequisites.sh --json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  ./check-prerequisites.sh --json --require-tasks --include-tasks

  # Extract compact data-model bootstrap packet for /sdd.plan.data-model
  ./check-prerequisites.sh --json --data-model-preflight

  # Extract compact tasks bootstrap packet for /sdd.tasks
  ./check-prerequisites.sh --json --task-preflight

  # Extract compact implementation bootstrap packet for /sdd.implement
  ./check-prerequisites.sh --json --require-tasks --include-tasks --implement-preflight
  
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

# Get feature paths and validate branch.
eval "$(get_feature_paths)"
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":%s,"BRANCH":%s,"FEATURE_DIR":%s,"FEATURE_SPEC":%s,"IMPL_PLAN":%s,"TASKS":%s,"TASKS_MANIFEST":%s}\n' \
            "$(json_string "$REPO_ROOT")" \
            "$(json_string "$CURRENT_BRANCH")" \
            "$(json_string "$FEATURE_DIR")" \
            "$(json_string "$FEATURE_SPEC")" \
            "$(json_string "$IMPL_PLAN")" \
            "$(json_string "$TASKS")" \
            "$(json_string "$TASKS_MANIFEST")"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo "FEATURE_SPEC: $FEATURE_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
        echo "TASKS: $TASKS"
        echo "TASKS_MANIFEST: $TASKS_MANIFEST"
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
if $DATA_MODEL_PREFLIGHT && ! $JSON_MODE; then
    echo "ERROR: --data-model-preflight requires --json output mode." >&2
    exit 1
fi

if $TASK_PREFLIGHT && ! $JSON_MODE; then
    echo "ERROR: --task-preflight requires --json output mode." >&2
    exit 1
fi

if $IMPLEMENT_PREFLIGHT && ! $JSON_MODE; then
    echo "ERROR: --implement-preflight requires --json output mode." >&2
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
    local_execution_protocol="$(build_local_execution_protocol_json)"
    SPECIFY_CMD="$(resolve_specify_cmd || true)"

    feature_json="$(json_string "$FEATURE_DIR")"
    anchor_gate_payload="{\"script_path\":$(json_string "scripts/implement_anchor_gate.py"),\"history_path\":$(json_string "$FEATURE_DIR/audits/implement-history.md")}"
    json_payload="{\"FEATURE_DIR\":${feature_json},\"AVAILABLE_DOCS\":${json_docs},\"LOCAL_EXECUTION_PROTOCOL\":${local_execution_protocol},\"IMPLEMENT_ANCHOR_GATE\":${anchor_gate_payload}"

    if $DATA_MODEL_PREFLIGHT; then
        data_model_bootstrap="null"
        if [[ -n "$SPECIFY_CMD" ]]; then
            if data_model_bootstrap="$("$SPECIFY_CMD" internal-data-model-bootstrap \
                --feature-dir "$FEATURE_DIR" \
                --plan "$IMPL_PLAN" \
                --spec "$FEATURE_SPEC" \
                --research "$RESEARCH" \
                --data-model "$DATA_MODEL")"; then
                :
            else
                data_model_bootstrap="null"
            fi
        fi
        json_payload="${json_payload},\"DATA_MODEL_BOOTSTRAP\":${data_model_bootstrap}"
    fi

    if $TASK_PREFLIGHT; then
        task_bootstrap="null"
        if [[ -n "$SPECIFY_CMD" ]]; then
            if task_bootstrap="$("$SPECIFY_CMD" internal-task-bootstrap \
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
    fi

    if $IMPLEMENT_PREFLIGHT; then
        implement_bootstrap="null"
        tasks_manifest_bootstrap="null"
        if [[ -n "$SPECIFY_CMD" ]]; then
            if implement_bootstrap="$("$SPECIFY_CMD" internal-implement-bootstrap \
                --feature-dir "$FEATURE_DIR" \
                --spec "$FEATURE_SPEC" \
                --plan "$IMPL_PLAN" \
                --tasks "$TASKS" \
                --analyze-history "$FEATURE_DIR/audits/analyze-history.md")"; then
                :
            else
                implement_bootstrap="null"
            fi

            if tasks_manifest_bootstrap="$("$SPECIFY_CMD" internal-tasks-manifest-bootstrap \
                --feature-dir "$FEATURE_DIR" \
                --plan "$IMPL_PLAN" \
                --tasks "$TASKS" \
                --tasks-manifest "$TASKS_MANIFEST")"; then
                :
            else
                tasks_manifest_bootstrap="null"
            fi
        fi
        json_payload="${json_payload},\"IMPLEMENT_BOOTSTRAP\":${implement_bootstrap}"
        json_payload="${json_payload},\"TASKS_MANIFEST_BOOTSTRAP\":${tasks_manifest_bootstrap}"
    fi

    if $TASK_PREFLIGHT; then
        json_payload="${json_payload},\"TASKS_BOOTSTRAP\":${task_bootstrap}"
    fi

    json_payload="${json_payload}}"
    printf '%s\n' "$json_payload"
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
