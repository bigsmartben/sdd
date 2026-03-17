#!/usr/bin/env bash
# Common functions and variables for all scripts

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi

    echo "main"  # Final fallback
}

# Check if we have git available
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    fi

    return 0
}

get_feature_dir() { echo "$1/specs/$2"; }

is_path_within_dir() {
    local path="$1"
    local root="$2"

    case "$path" in
        "$root" | "$root"/*) return 0 ;;
        *) return 1 ;;
    esac
}

resolve_repo_relative_path() {
    local repo_root="$1"
    local input_path="$2"

    if [[ -z "$input_path" ]]; then
        return 1
    fi

    local candidate="$input_path"
    if [[ "$candidate" != /* ]]; then
        candidate="$repo_root/$candidate"
    fi

    local parent_dir
    parent_dir="$(dirname "$candidate")"
    if [[ ! -d "$parent_dir" ]]; then
        return 1
    fi

    printf '%s/%s\n' "$(cd "$parent_dir" && pwd -P)" "$(basename "$candidate")"
}

resolve_feature_file_path() {
    local repo_root="$1"
    local raw_path="$2"
    local expected_name="$3"
    local label="$4"

    local specs_root="$repo_root/specs"
    if [[ ! -d "$specs_root" ]]; then
        echo "ERROR: specs directory not found: $specs_root" >&2
        return 1
    fi

    local resolved_path
    resolved_path="$(resolve_repo_relative_path "$repo_root" "$raw_path")" || {
        echo "ERROR: Unable to resolve $label path: $raw_path" >&2
        return 1
    }

    local resolved_specs_root
    resolved_specs_root="$(cd "$specs_root" && pwd -P)"

    if ! is_path_within_dir "$resolved_path" "$resolved_specs_root"; then
        echo "ERROR: $label must be located under $resolved_specs_root" >&2
        return 1
    fi

    if [[ "$(basename "$resolved_path")" != "$expected_name" ]]; then
        echo "ERROR: $label must point to a file named $expected_name: $resolved_path" >&2
        return 1
    fi

    if [[ ! -f "$resolved_path" ]]; then
        echo "ERROR: $label not found: $resolved_path" >&2
        return 1
    fi

    echo "$resolved_path"
}

json_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    value="${value//$'\r'/\\r}"
    value="${value//$'\t'/\\t}"
    value="${value//$'\f'/\\f}"
    value="${value//$'\b'/\\b}"
    printf '%s' "$value"
}

json_string() {
    printf '"%s"' "$(json_escape "$1")"
}

json_array() {
    local first=true
    local item

    printf '['
    for item in "$@"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            printf ','
        fi
        json_string "$item"
    done
    printf ']'
}

emit_feature_paths() {
    local repo_root="$1"
    local current_branch="$2"
    local has_git_repo="$3"
    local feature_dir="$4"
    local feature_spec="$5"
    local impl_plan="$6"

    printf 'REPO_ROOT=%q\n' "$repo_root"
    printf 'CURRENT_BRANCH=%q\n' "$current_branch"
    printf 'HAS_GIT=%q\n' "$has_git_repo"
    printf 'FEATURE_DIR=%q\n' "$feature_dir"
    printf 'FEATURE_SPEC=%q\n' "$feature_spec"
    printf 'IMPL_PLAN=%q\n' "$impl_plan"
    printf 'TASKS=%q\n' "$feature_dir/tasks.md"
    printf 'RESEARCH=%q\n' "$feature_dir/research.md"
    printf 'DATA_MODEL=%q\n' "$feature_dir/data-model.md"
    printf 'TEST_MATRIX=%q\n' "$feature_dir/test-matrix.md"
    printf 'CONTRACTS_DIR=%q\n' "$feature_dir/contracts"
}

get_feature_paths_from_spec_file() {
    local raw_spec_path="$1"
    local repo_root
    repo_root="$(get_repo_root)"
    local current_branch
    current_branch="$(get_current_branch)"
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    local feature_spec
    feature_spec="$(resolve_feature_file_path "$repo_root" "$raw_spec_path" "spec.md" "spec file")" || return 1
    local feature_dir
    feature_dir="$(dirname "$feature_spec")"

    emit_feature_paths "$repo_root" "$current_branch" "$has_git_repo" "$feature_dir" "$feature_spec" "$feature_dir/plan.md"
}

get_feature_paths_from_plan_file() {
    local raw_plan_path="$1"
    local repo_root
    repo_root="$(get_repo_root)"
    local current_branch
    current_branch="$(get_current_branch)"
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    local impl_plan
    impl_plan="$(resolve_feature_file_path "$repo_root" "$raw_plan_path" "plan.md" "plan file")" || return 1
    local feature_dir
    feature_dir="$(dirname "$impl_plan")"

    emit_feature_paths "$repo_root" "$current_branch" "$has_git_repo" "$feature_dir" "$feature_dir/spec.md" "$impl_plan"
}

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir="$repo_root/specs"

    # Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    if [[ ! "$branch_name" =~ ^([0-9]{3})- ]]; then
        # If branch doesn't have numeric prefix, fall back to exact match
        echo "$specs_dir/$branch_name"
        return
    fi

    local prefix="${BASH_REMATCH[1]}"

    # Search for directories in specs/ that start with this prefix
    local matches=()
    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/"$prefix"-*; do
            if [[ -d "$dir" ]]; then
                matches+=("$(basename "$dir")")
            fi
        done
    fi

    # Handle results
    if [[ ${#matches[@]} -eq 0 ]]; then
        # No match found - return the branch name path (will fail later with clear error)
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        # Exactly one match - perfect!
        echo "$specs_dir/${matches[0]}"
    else
        # Multiple matches - this shouldn't happen with proper naming convention
        echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
        echo "Please ensure only one spec directory exists per numeric prefix." >&2
        echo "$specs_dir/$branch_name"  # Return something to avoid breaking the script
    fi
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # Use prefix-based lookup to support multiple branches per spec
    local feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")

    emit_feature_paths "$repo_root" "$current_branch" "$has_git_repo" "$feature_dir" "$feature_dir/spec.md" "$feature_dir/plan.md"
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
