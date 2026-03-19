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

    # For non-git repos, try to find the latest date-keyed feature directory.
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        local feature_dirs=()
        local latest_feature=""
        local highest_date=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                feature_dirs+=("$dirname")
                if [[ "$dirname" =~ ^([0-9]{8})- ]]; then
                    local date_key=${BASH_REMATCH[1]}
                    date_key=$((10#$date_key))
                    if [[ "$date_key" -gt "$highest_date" ]]; then
                        highest_date=$date_key
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ "${#feature_dirs[@]}" -eq 1 ]]; then
            echo "${feature_dirs[0]}"
            return
        fi

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
    local branch_leaf="${branch##*/}"
    local preferred_pattern='^feature-[0-9]{8}-[a-z0-9][a-z0-9-]*$'
    local normalized_pattern='^[0-9]{8}-[a-z0-9][a-z0-9-]*$'
    local legacy_pattern='^[0-9]+-[a-z0-9][a-z0-9-]*$'
    local legacy_ordinal_pattern='^[0-9]{3}-[a-z0-9][a-z0-9-]*$'

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        if [[ "$branch_leaf" =~ $legacy_pattern && ! "$branch_leaf" =~ $normalized_pattern && ! "$branch_leaf" =~ $legacy_ordinal_pattern ]]; then
            echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
            echo "Feature branches should be named like: feature-20250708-parent-hanxue-channel" >&2
            return 1
        fi
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    if [[ "$branch_leaf" =~ $preferred_pattern ]]; then
        return 0
    fi
    if [[ "$branch_leaf" =~ $normalized_pattern ]]; then
        return 0
    fi
    if [[ "$branch_leaf" =~ $legacy_ordinal_pattern ]]; then
        return 0
    fi

    echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
    echo "Feature branches should be named like: feature-20250708-parent-hanxue-channel" >&2
    return 1
}

get_feature_dir() { echo "$1/specs/$2"; }

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

# Resolve feature directory from branch naming rules.
# Preferred: feature-YYYYMMDD-slug -> specs/YYYYMMDD-slug
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir="$repo_root/specs"
    local branch_leaf="${branch_name##*/}"

    # Preferred naming: feature-YYYYMMDD-slug -> specs/YYYYMMDD-slug
    if [[ "$branch_leaf" =~ ^feature-([0-9]{8}-[a-z0-9][a-z0-9-]*)$ ]]; then
        echo "$specs_dir/${BASH_REMATCH[1]}"
        return
    fi

    # Accept already normalized feature key as branch leaf.
    if [[ "$branch_leaf" =~ ^([0-9]{8}-[a-z0-9][a-z0-9-]*)$ ]]; then
        echo "$specs_dir/${BASH_REMATCH[1]}"
        return
    fi

    # Legacy compatibility: allow 3-digit feature branches to map by numeric prefix.
    if [[ "$branch_leaf" =~ ^([0-9]{3})- ]]; then
        local prefix="${BASH_REMATCH[1]}"
        local matches=()
        if [[ -d "$specs_dir" ]]; then
            for dir in "$specs_dir"/"$prefix"-*; do
                if [[ -d "$dir" ]]; then
                    matches+=("$(basename "$dir")")
                fi
            done
        fi

        if [[ ${#matches[@]} -eq 1 ]]; then
            echo "$specs_dir/${matches[0]}"
            return
        fi
        if [[ ${#matches[@]} -gt 1 ]]; then
            echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
            echo "Please ensure only one spec directory exists per numeric prefix." >&2
        fi
    fi

    echo "$specs_dir/$branch_leaf"
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
