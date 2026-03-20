#!/usr/bin/env bash

set -e

JSON_MODE=false
SHORT_NAME=""
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --short-name)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --short-name requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            # Check if the next argument is another option (starts with --)
            if [[ "$next_arg" == --* ]]; then
                echo 'Error: --short-name requires a value' >&2
                exit 1
            fi
            SHORT_NAME="$next_arg"
            ;;
        --number)
            echo 'Error: --number is not supported. Use unified naming: feature-YYYYMMDD-slug.' >&2
            exit 1
            ;;
        --help|-h) 
            echo "Usage: $0 [--json] [--short-name <name>] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --short-name <name> Provide a custom short name (2-4 words) for branch naming"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 'Add user authentication system' --short-name 'user-auth'"
            echo "  $0 'Implement OAuth2 integration for API' --short-name 'oauth2-api'"
            exit 0
            ;;
        --*)
            echo "Error: Unknown option: $arg" >&2
            exit 1
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
    i=$((i + 1))
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] [--short-name <name>] <feature_description>" >&2
    exit 1
fi

# Trim whitespace and validate description is not empty (e.g., user passed only whitespace)
FEATURE_DESCRIPTION=$(echo "$FEATURE_DESCRIPTION" | xargs)
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Error: Feature description cannot be empty or contain only whitespace" >&2
    exit 1
fi

# Function to find the repository root by searching for existing project markers
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

current_date_key() {
    date +%Y%m%d
}

# Best-effort remote sync that avoids interactive/network hangs.
# Behavior controls:
# - SPECIFY_SKIP_FETCH=1      -> skip remote fetch entirely
# - SPECIFY_FETCH_TIMEOUT=<s> -> timeout seconds (default: 8)
# - SPECIFY_FETCH_MODE=<mode> -> preferred (default), all, none
safe_fetch_remote_branches() {
    if [ "${SPECIFY_SKIP_FETCH:-0}" = "1" ] || [ "${SPECIFY_FETCH_MODE:-preferred}" = "none" ]; then
        >&2 echo "[specify] Warning: skipping remote fetch (SPECIFY_SKIP_FETCH=1 or SPECIFY_FETCH_MODE=none)"
        return 0
    fi

    local fetch_timeout="${SPECIFY_FETCH_TIMEOUT:-8}"
    local ssh_cmd="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=5}"
    local fetch_mode="${SPECIFY_FETCH_MODE:-preferred}"
    local remotes=""

    remotes=$(git remote 2>/dev/null || true)
    if [ -z "$remotes" ]; then
        return 0
    fi

    local fetch_target=("--all")
    if [ "$fetch_mode" != "all" ]; then
        # Prefer the most common primary remote to avoid slow fan-out fetches.
        local preferred_remote=""
        if echo "$remotes" | grep -qx "origin"; then
            preferred_remote="origin"
        else
            preferred_remote=$(echo "$remotes" | head -n1)
        fi
        fetch_target=("$preferred_remote")
    fi

    if command -v timeout >/dev/null 2>&1; then
        GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="$ssh_cmd" \
            timeout "${fetch_timeout}s" \
            git -c credential.interactive=never fetch "${fetch_target[@]}" --prune --no-tags --quiet >/dev/null 2>&1 || \
            >&2 echo "[specify] Warning: git fetch skipped/failed (timeout or network issue); using local branch/spec data"
    elif command -v gtimeout >/dev/null 2>&1; then
        GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="$ssh_cmd" \
            gtimeout "${fetch_timeout}s" \
            git -c credential.interactive=never fetch "${fetch_target[@]}" --prune --no-tags --quiet >/dev/null 2>&1 || \
            >&2 echo "[specify] Warning: git fetch skipped/failed (timeout or network issue); using local branch/spec data"
    else
        GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="$ssh_cmd" \
            git -c credential.interactive=never fetch "${fetch_target[@]}" --prune --no-tags --quiet >/dev/null 2>&1 || \
            >&2 echo "[specify] Warning: git fetch failed; using local branch/spec data"
    fi
}

find_remote_branch_ref() {
    local branch_name="$1"
    local remote_refs=""

    remote_refs=$(git for-each-ref --format='%(refname:short)' "refs/remotes/*/$branch_name" 2>/dev/null || true)
    if [ -z "$remote_refs" ]; then
        return 1
    fi

    if echo "$remote_refs" | grep -qx "origin/$branch_name"; then
        echo "origin/$branch_name"
        return 0
    fi

    echo "$remote_refs" | head -n1
    return 0
}

# Function to clean and format a branch name
clean_branch_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
if [[ ! -r "$TEMPLATE" ]]; then
    echo "Error: Required runtime template not found or not readable at $TEMPLATE" >&2
    exit 1
fi

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Function to generate branch name with stop word filtering and length filtering
generate_branch_name() {
    local description="$1"
    
    # Common stop words to filter out
    local stop_words="^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$"
    
    # Convert to lowercase and split into words
    local clean_name=$(echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/ /g')
    
    # Filter words: remove stop words and words shorter than 3 chars (unless they're uppercase acronyms in original)
    local meaningful_words=()
    for word in $clean_name; do
        # Skip empty words
        [ -z "$word" ] && continue
        
        # Keep words that are NOT stop words AND (length >= 3 OR are potential acronyms)
        if ! echo "$word" | grep -qiE "$stop_words"; then
            if [ ${#word} -ge 3 ]; then
                meaningful_words+=("$word")
            elif echo "$description" | grep -q "\b${word^^}\b"; then
                # Keep short words if they appear as uppercase in original (likely acronyms)
                meaningful_words+=("$word")
            fi
        fi
    done
    
    # If we have meaningful words, use first 3-4 of them
    if [ ${#meaningful_words[@]} -gt 0 ]; then
        local max_words=3
        if [ ${#meaningful_words[@]} -eq 4 ]; then max_words=4; fi
        
        local result=""
        local count=0
        for word in "${meaningful_words[@]}"; do
            if [ $count -ge $max_words ]; then break; fi
            if [ -n "$result" ]; then result="$result-"; fi
            result="$result$word"
            count=$((count + 1))
        done
        echo "$result"
    else
        # Fallback to original logic if no meaningful words found
        local cleaned=$(clean_branch_name "$description")
        echo "$cleaned" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//'
    fi
}

# Generate fallback branch suffix
if [ -n "$SHORT_NAME" ]; then
    BRANCH_SUFFIX=$(clean_branch_name "$SHORT_NAME")
else
    BRANCH_SUFFIX=$(generate_branch_name "$FEATURE_DESCRIPTION")
fi

FEATURE_DATE=$(current_date_key)
BRANCH_PREFIX="feature-${FEATURE_DATE}-"
BRANCH_NAME="${BRANCH_PREFIX}${BRANCH_SUFFIX}"

MAX_BRANCH_LENGTH=244
if [ ${#BRANCH_NAME} -gt $MAX_BRANCH_LENGTH ]; then
    MAX_SUFFIX_LENGTH=$((MAX_BRANCH_LENGTH - ${#BRANCH_PREFIX}))
    TRUNCATED_SUFFIX=$(echo "$BRANCH_SUFFIX" | cut -c1-$MAX_SUFFIX_LENGTH)
    TRUNCATED_SUFFIX=$(echo "$TRUNCATED_SUFFIX" | sed 's/-$//')

    ORIGINAL_BRANCH_NAME="$BRANCH_NAME"
    BRANCH_NAME="${BRANCH_PREFIX}${TRUNCATED_SUFFIX}"

    >&2 echo "[specify] Warning: Branch name exceeded GitHub's 244-byte limit"
    >&2 echo "[specify] Original: $ORIGINAL_BRANCH_NAME (${#ORIGINAL_BRANCH_NAME} bytes)"
    >&2 echo "[specify] Truncated to: $BRANCH_NAME (${#BRANCH_NAME} bytes)"
fi

FEATURE_PREFIX="${BRANCH_NAME%%-*}"
if echo "$BRANCH_NAME" | grep -qE '^feature-([0-9]{8})-'; then
    FEATURE_NUM=$(echo "$BRANCH_NAME" | sed -E 's/^feature-([0-9]{8})-.*/\1/')
else
    FEATURE_NUM="000"
fi

FEATURE_KEY="$BRANCH_NAME"
if echo "$BRANCH_NAME" | grep -qE '^feature-([0-9]{8}-[a-z0-9][a-z0-9-]*)$'; then
    FEATURE_KEY=$(echo "$BRANCH_NAME" | sed -E 's/^feature-([0-9]{8}-[a-z0-9][a-z0-9-]*)$/\1/')
fi

if [ "$HAS_GIT" = true ]; then
    CURRENT_HEAD="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    if [ "$CURRENT_HEAD" != "$BRANCH_NAME" ]; then
        if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
            if ! git checkout "$BRANCH_NAME" >/dev/null 2>&1; then
                >&2 echo "Error: Failed to switch to git branch '$BRANCH_NAME'. Please check your git configuration and try again."
                exit 1
            fi
        else
            safe_fetch_remote_branches
            REMOTE_REF="$(find_remote_branch_ref "$BRANCH_NAME" || true)"
            if [ -n "$REMOTE_REF" ]; then
                if ! git checkout --track "$REMOTE_REF" >/dev/null 2>&1; then
                    >&2 echo "Error: Failed to switch to git branch '$BRANCH_NAME' from remote '$REMOTE_REF'. Please check your git configuration and try again."
                    exit 1
                fi
            else
                if ! git checkout -b "$BRANCH_NAME" >/dev/null 2>&1; then
                    >&2 echo "Error: Failed to create and switch to git branch '$BRANCH_NAME'. Please check your git configuration and try again."
                    exit 1
                fi
            fi
        fi
    fi
fi

FEATURE_DIR="$SPECS_DIR/$FEATURE_KEY"
mkdir -p "$FEATURE_DIR"

SPEC_FILE="$FEATURE_DIR/spec.md"
cp "$TEMPLATE" "$SPEC_FILE"

# Set the SPECIFY_FEATURE environment variable for the current session
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
