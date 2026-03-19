#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
FEATURE_DIR=""
RULES_PATH=""

print_help() {
    cat <<'EOF'
Usage: run-planning-lint.sh --feature-dir <abs-path> --rules <abs-path> [--json] [--help]

Run planning mechanical lint checks from a TSV rules catalog.

Options:
  --feature-dir <abs-path>   Absolute path to feature directory (e.g. /repo/specs/20250708-feature)
  --rules <abs-path>         Absolute path to rules TSV catalog
  --json                     Output machine-readable JSON
  --help                     Show this help message

Supported rule kinds:
  - file_regex_forbidden
  - file_regex_required_any
  - component_symbols_exist
  - anchor_status_allowed_values
  - northbound_controller_required
  - repo_anchor_paths_exist
  - plan_status_consistency
  - binding_projection_stable_only
  - binding_tuple_projection_sync
EOF
}

error() {
    echo "ERROR: $*" >&2
}

is_abs_path() {
    [[ "$1" == /* || "$1" =~ ^[A-Za-z]:/ ]]
}

normalize_fs_path() {
    local path="$1"

    if [[ "$path" =~ ^[A-Za-z]:/ ]]; then
        if command -v wslpath >/dev/null 2>&1; then
            wslpath "$path"
            return 0
        fi
        if command -v cygpath >/dev/null 2>&1; then
            cygpath -u "$path"
            return 0
        fi

        local drive="${path:0:1}"
        local tail="${path:2}"
        drive="$(echo "$drive" | tr '[:upper:]' '[:lower:]')"
        printf '/mnt/%s%s\n' "$drive" "$tail"
        return 0
    fi

    printf '%s\n' "$path"
}

detect_repo_root() {
    local feature_dir="$1"
    local parent_dir
    parent_dir="$(dirname "$feature_dir")"

    if [[ "$(basename "$parent_dir")" == "specs" ]]; then
        dirname "$parent_dir"
        return 0
    fi

    printf '%s\n' "$parent_dir"
}

resolve_anchor_target_path() {
    local repo_root="$1"
    local anchor_path="$2"
    local normalized_path="${anchor_path//\\//}"

    if [[ "$normalized_path" =~ ^[A-Za-z]:/ || "$normalized_path" == /* ]]; then
        normalize_fs_path "$normalized_path"
        return 0
    fi

    printf '%s/%s\n' "$repo_root" "$normalized_path"
}

trim() {
    local value="$1"
    # shellcheck disable=SC2001
    value="$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    printf '%s' "$value"
}

parse_markdown_cells() {
    local line="$1"
    MARKDOWN_CELLS=()

    if [[ ! "$line" =~ ^[[:space:]]*\|.*\|[[:space:]]*$ ]]; then
        return 1
    fi

    local line_trimmed
    local content
    local cell=''
    local escaped=false
    local idx
    local ch

    line_trimmed="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    content="${line_trimmed#|}"
    content="${content%|}"

    for ((idx = 0; idx < ${#content}; idx++)); do
        ch="${content:idx:1}"

        if [[ "$escaped" == true ]]; then
            if [[ "$ch" == "|" || "$ch" == "\\" ]]; then
                cell+="$ch"
            else
                cell+="\\$ch"
            fi
            escaped=false
            continue
        fi

        if [[ "$ch" == "\\" ]]; then
            escaped=true
            continue
        fi

        if [[ "$ch" == "|" ]]; then
            MARKDOWN_CELLS+=("$(trim "$cell")")
            cell=''
            continue
        fi

        cell+="$ch"
    done

    if [[ "$escaped" == true ]]; then
        cell+="\\"
    fi
    MARKDOWN_CELLS+=("$(trim "$cell")")
    return 0
}

json_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    printf '%s' "$s"
}

get_param() {
    local params="$1"
    local key="$2"
    local part
    local k
    local v

    IFS=';' read -r -a parts <<< "$params"
    for part in "${parts[@]}"; do
        [[ -z "$part" ]] && continue
        k="${part%%=*}"
        v="${part#*=}"
        k="$(trim "$k")"
        if [[ "$k" == "$key" ]]; then
            printf '%s' "$(trim "$v")"
            return 0
        fi
    done

    printf ''
}

normalize_regex_for_grep() {
    local raw="$1"
    local __out_regex_ref="$2"
    local __out_case_insensitive_ref="$3"

    local regex="$raw"
    local case_insensitive="false"

    if [[ "$regex" == "(?i)"* ]]; then
        case_insensitive="true"
        regex="${regex#(?i)}"
    fi

    # grep -E does not support PCRE non-capturing groups; downgrade them to
    # plain capture groups so one rules catalog can serve bash and PowerShell.
    regex="${regex//\(\?:/(}"

    printf -v "$__out_regex_ref" '%s' "$regex"
    printf -v "$__out_case_insensitive_ref" '%s' "$case_insensitive"
}

stream_file_for_grep() {
    local file_path="$1"
    sed 's/\r$//' "$file_path"
}

contains_value() {
    local needle="$1"
    shift
    local item

    for item in "$@"; do
        if [[ "$item" == "$needle" ]]; then
            return 0
        fi
    done

    return 1
}

validate_anchor_status_fragment() {
    local fragment="$1"
    local __allowed_csv="$2"
    local __out_error_ref="$3"

    local fragment_no_backticks
    local -a raw_tokens=()
    local -a candidate_tokens=()
    local -a invalid_tokens=()
    local -a allowed_tokens_raw=()
    local -a allowed_tokens=()
    local token
    local token_lower
    local has_allowed=false
    local has_candidate=false

    IFS=',' read -r -a allowed_tokens_raw <<< "$__allowed_csv"
    for token in "${allowed_tokens_raw[@]}"; do
        token_lower="$(echo "$token" | tr '[:upper:]' '[:lower:]')"
        token_lower="$(trim "$token_lower")"
        [[ -n "$token_lower" ]] && allowed_tokens+=("$token_lower")
    done

    if grep -q '`' <<< "$fragment"; then
        while IFS= read -r token; do
            [[ -z "$token" ]] && continue
            raw_tokens+=("$token")
        done < <(grep -oE '`[^`]+`' <<< "$fragment" | sed 's/^`//;s/`$//' || true)
    fi

    if [[ ${#raw_tokens[@]} -eq 0 ]]; then
        fragment_no_backticks="${fragment//\`/ }"
        while IFS= read -r token; do
            [[ -z "$token" ]] && continue
            raw_tokens+=("$token")
        done < <(grep -oE '[A-Za-z][A-Za-z_-]*' <<< "$fragment_no_backticks" || true)
    fi

    for token in "${raw_tokens[@]}"; do
        token_lower="$(echo "$token" | tr '[:upper:]' '[:lower:]')"
        token_lower="$(trim "$token_lower")"
        [[ -z "$token_lower" ]] && continue

        case "$token_lower" in
            anchor|status|repo|boundary|implementation|entry|required|legacy|or|and)
                continue
                ;;
        esac

        has_candidate=true
        candidate_tokens+=("$token_lower")
    done

    if [[ "$has_candidate" == false ]]; then
        printf -v "$__out_error_ref" '%s' "Anchor Status field is present but no status token was detected."
        return 1
    fi

    for token in "${candidate_tokens[@]}"; do
        if contains_value "$token" "${allowed_tokens[@]}"; then
            has_allowed=true
        else
            invalid_tokens+=("$token")
        fi
    done

    if [[ ${#invalid_tokens[@]} -gt 0 ]]; then
        printf -v "$__out_error_ref" '%s' "Invalid status token(s): $(IFS=','; echo "${invalid_tokens[*]}"). Allowed: $(
            IFS=','
            echo "${allowed_tokens[*]}"
        )"
        return 1
    fi

    if [[ ${#candidate_tokens[@]} -ne 1 ]]; then
        printf -v "$__out_error_ref" '%s' "Anchor Status must contain exactly one status token. Found: $(IFS=','; echo "${candidate_tokens[*]}")."
        return 1
    fi

    if [[ "$has_allowed" == false ]]; then
        printf -v "$__out_error_ref" '%s' "No allowed status token found. Allowed: $(IFS=','; echo "${allowed_tokens[*]}")"
        return 1
    fi

    printf -v "$__out_error_ref" '%s' ""
    return 0
}

evaluate_northbound_anchor_pair() {
    local boundary_value="$1"
    local entry_value="$2"
    local boundary_http_regex="$3"
    local boundary_forbidden_regex="$4"
    local entry_controller_regex="$5"
    local entry_forbidden_regex="$6"
    local __out_detail_ref="$7"

    local boundary entry
    boundary="$(trim "$boundary_value")"
    entry="$(trim "$entry_value")"

    if [[ -z "$boundary" ]]; then
        printf -v "$__out_detail_ref" '%s' ""
        return 1
    fi

    if grep -qiE "$boundary_forbidden_regex" <<< "$boundary"; then
        printf -v "$__out_detail_ref" '%s' "Boundary Anchor resolves to facade/service-style symbol while controller-first HTTP entry is required by feature layering."
        return 0
    fi

    if grep -qiE "$boundary_http_regex" <<< "$boundary"; then
        if [[ -z "$entry" ]]; then
            printf -v "$__out_detail_ref" '%s' "HTTP Boundary Anchor requires an Implementation Entry Anchor that resolves to the owning controller method."
            return 0
        fi

        if ! grep -qiE "$entry_controller_regex" <<< "$entry"; then
            printf -v "$__out_detail_ref" '%s' "HTTP Boundary Anchor is paired with a non-controller Implementation Entry Anchor."
            return 0
        fi

        if grep -qiE "$entry_forbidden_regex" <<< "$entry" && ! grep -qiE "$entry_controller_regex" <<< "$entry"; then
            printf -v "$__out_detail_ref" '%s' "HTTP Boundary Anchor is paired with service/facade-style Implementation Entry Anchor instead of the owning controller method."
            return 0
        fi
    fi

    printf -v "$__out_detail_ref" '%s' ""
    return 1
}

normalize_markdown_scalar() {
    local value
    value="$(trim "$1")"
    value="${value//\`/}"
    printf '%s' "$(trim "$value")"
}

normalize_markdown_list_cell() {
    local value
    value="$(normalize_markdown_scalar "$1")"
    value="${value#[}"
    value="${value%]}"
    value="$(echo "$value" | sed 's/[[:space:]]*,[[:space:]]*/,/g;s/^[[:space:]]*//;s/[[:space:]]*$//')"
    printf '%s' "$value"
}

extract_anchor_status_token() {
    local raw normalized token
    raw="$1"
    normalized="$(normalize_markdown_scalar "$raw")"
    normalized="$(echo "$normalized" | tr '[:upper:]' '[:lower:]')"

    for token in existing extended new todo; do
        if grep -qiE "(^|[^A-Za-z])${token}([^A-Za-z]|$)" <<< "$normalized"; then
            printf '%s' "$token"
            return 0
        fi
    done

    printf ''
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --feature-dir)
                [[ $# -lt 2 ]] && { error "--feature-dir requires a value"; exit 1; }
                FEATURE_DIR="$2"
                shift 2
                ;;
            --rules)
                [[ $# -lt 2 ]] && { error "--rules requires a value"; exit 1; }
                RULES_PATH="$2"
                shift 2
                ;;
            --json)
                JSON_MODE=true
                shift
                ;;
            --help|-h)
                print_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                print_help >&2
                exit 1
                ;;
        esac
    done
}

parse_args "$@"

if [[ -z "$FEATURE_DIR" || -z "$RULES_PATH" ]]; then
    error "Both --feature-dir and --rules are required"
    print_help >&2
    exit 1
fi

if ! is_abs_path "$FEATURE_DIR"; then
    error "--feature-dir must be an absolute path"
    exit 1
fi

if ! is_abs_path "$RULES_PATH"; then
    error "--rules must be an absolute path"
    exit 1
fi

FEATURE_DIR="$(normalize_fs_path "$FEATURE_DIR")"
RULES_PATH="$(normalize_fs_path "$RULES_PATH")"

if [[ ! -d "$FEATURE_DIR" ]]; then
    error "Feature directory not found: $FEATURE_DIR"
    exit 1
fi

if [[ ! -f "$RULES_PATH" ]]; then
    error "Rules catalog not found: $RULES_PATH"
    exit 1
fi

REPO_ROOT_FOR_FEATURE="$(detect_repo_root "$FEATURE_DIR")"

mapfile -t ALL_REL_FILES < <(cd "$FEATURE_DIR" && find . -type f -print | sed 's|^\./||' | sort)

rules_total=0
rules_evaluated=0
findings_total=0
findings_json_items=()
declare -A severity_counts=()

increment_severity_count() {
    local sev_raw="$1"
    local sev
    sev="$(echo "$sev_raw" | tr '[:lower:]' '[:upper:]')"
    [[ -z "$sev" ]] && sev="UNKNOWN"
    severity_counts["$sev"]=$(( ${severity_counts["$sev"]:-0} + 1 ))
}

add_finding() {
    local rule_id="$1"
    local severity="$2"
    local file="$3"
    local line="$4"
    local message="$5"
    local remediation="$6"

    findings_total=$((findings_total + 1))
    increment_severity_count "$severity"

    local escaped_rule_id escaped_severity escaped_file escaped_message escaped_remediation
    escaped_rule_id="$(json_escape "$rule_id")"
    escaped_severity="$(json_escape "$severity")"
    escaped_file="$(json_escape "$file")"
    escaped_message="$(json_escape "$message")"
    escaped_remediation="$(json_escape "$remediation")"

    findings_json_items+=("{\"rule_id\":\"$escaped_rule_id\",\"severity\":\"$escaped_severity\",\"source\":\"lint\",\"file\":\"$escaped_file\",\"line\":$line,\"message\":\"$escaped_message\",\"remediation\":\"$escaped_remediation\"}")
}

get_matching_files() {
    local pattern="$1"
    local rel

    for rel in "${ALL_REL_FILES[@]}"; do
        if [[ "$rel" == $pattern ]]; then
            printf '%s\n' "$FEATURE_DIR/$rel"
        fi
    done
}

while IFS= read -r raw_rule_line || [[ -n "$raw_rule_line" ]]; do
    raw_rule_line="${raw_rule_line%$'\r'}"
    IFS=$'\x1f' read -r id enabled severity scope glob kind params message remediation _ <<< "${raw_rule_line//$'\t'/$'\x1f'}"
    [[ -z "${id:-}" ]] && continue
    [[ "$id" == "id" ]] && continue
    [[ "$id" =~ ^# ]] && continue

    rules_total=$((rules_total + 1))

    enabled_normalized="$(echo "$enabled" | tr '[:upper:]' '[:lower:]')"
    if [[ "$enabled_normalized" != "true" ]]; then
        continue
    fi

    rules_evaluated=$((rules_evaluated + 1))

    mapfile -t matched_files < <(get_matching_files "$glob")

    case "$kind" in
        file_regex_forbidden)
            regex="$(get_param "$params" "regex")"
            if [[ -z "$regex" ]]; then
                add_finding "$id" "$severity" "$glob" 0 "Rule params missing required key: regex" "Fix rules TSV params for this rule."
                continue
            fi

            normalized_regex=""
            case_insensitive="false"
            normalize_regex_for_grep "$regex" normalized_regex case_insensitive

            for file_path in "${matched_files[@]}"; do
                if [[ "$case_insensitive" == "true" ]]; then
                    while IFS= read -r match_line; do
                        [[ -z "$match_line" ]] && continue
                        line_no="${match_line%%:*}"
                        rel_file="${file_path#$FEATURE_DIR/}"
                        add_finding "$id" "$severity" "$rel_file" "$line_no" "$message" "$remediation"
                    done < <(stream_file_for_grep "$file_path" | grep -niE "$normalized_regex" || true)
                else
                    while IFS= read -r match_line; do
                        [[ -z "$match_line" ]] && continue
                        line_no="${match_line%%:*}"
                        rel_file="${file_path#$FEATURE_DIR/}"
                        add_finding "$id" "$severity" "$rel_file" "$line_no" "$message" "$remediation"
                    done < <(stream_file_for_grep "$file_path" | grep -nE "$normalized_regex" || true)
                fi
            done
            ;;

        file_regex_required_any)
            regex="$(get_param "$params" "regex")"
            if [[ -z "$regex" ]]; then
                add_finding "$id" "$severity" "$glob" 0 "Rule params missing required key: regex" "Fix rules TSV params for this rule."
                continue
            fi

            normalized_regex=""
            case_insensitive="false"
            normalize_regex_for_grep "$regex" normalized_regex case_insensitive

            found_any=false
            for file_path in "${matched_files[@]}"; do
                if [[ "$case_insensitive" == "true" ]]; then
                    if stream_file_for_grep "$file_path" | grep -qiE "$normalized_regex"; then
                        found_any=true
                        break
                    fi
                else
                    if stream_file_for_grep "$file_path" | grep -qE "$normalized_regex"; then
                        found_any=true
                        break
                    fi
                fi
            done

            if [[ "$found_any" == false ]]; then
                target_file="$glob"
                if [[ ${#matched_files[@]} -gt 0 ]]; then
                    target_file="${matched_files[0]#$FEATURE_DIR/}"
                fi
                add_finding "$id" "$severity" "$target_file" 0 "$message" "$remediation"
            fi
            ;;

        component_symbols_exist)
            target_rel="$(get_param "$params" "file")"
            symbols_csv="$(get_param "$params" "symbols")"

            if [[ -z "$target_rel" || -z "$symbols_csv" ]]; then
                add_finding "$id" "$severity" "$glob" 0 "Rule params missing required key: file and/or symbols" "Fix rules TSV params for this rule."
                continue
            fi

            target_file="$FEATURE_DIR/$target_rel"
            if [[ ! -f "$target_file" ]]; then
                add_finding "$id" "$severity" "$target_rel" 0 "$message" "$remediation"
                continue
            fi

            missing_symbols=()
            IFS=',' read -r -a symbols <<< "$symbols_csv"
            for symbol in "${symbols[@]}"; do
                symbol_trimmed="$(trim "$symbol")"
                [[ -z "$symbol_trimmed" ]] && continue
                if ! stream_file_for_grep "$target_file" | grep -Fq -- "$symbol_trimmed"; then
                    missing_symbols+=("$symbol_trimmed")
                fi
            done

            if [[ ${#missing_symbols[@]} -gt 0 ]]; then
                missing_joined="$(IFS=','; echo "${missing_symbols[*]}")"
                add_finding "$id" "$severity" "$target_rel" 0 "$message Missing symbols: $missing_joined" "$remediation"
            fi
            ;;

        anchor_status_allowed_values)
            allowed_csv="$(get_param "$params" "allowed")"
            if [[ -z "$allowed_csv" ]]; then
                add_finding "$id" "$severity" "$glob" 0 "Rule params missing required key: allowed" "Fix rules TSV params for this rule."
                continue
            fi

            old_nocasematch="$(shopt -p nocasematch || true)"
            shopt -s nocasematch
            label_regex='^[[:space:]]*([-*][[:space:]]*)?(\*\*)?(Repo[ _-]*Anchor[ _-]*Status|Boundary[ _-]*Anchor[ _-]*Status|Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Status|Anchor[ _-]*Status)([[:space:]]*\([^)]*\))?(\*\*)?[[:space:]]*:[[:space:]]*(.+)$'
            table_header_regex='(Repo[ _-]*Anchor[ _-]*Status|Boundary[ _-]*Anchor[ _-]*Status|Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Status|Anchor[ _-]*Status)'

            for file_path in "${matched_files[@]}"; do
                rel_file="${file_path#$FEATURE_DIR/}"
                line_no=0
                in_table=false
                table_status_idx=-1

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))

                    if [[ "$line" =~ $label_regex ]]; then
                        status_fragment="${BASH_REMATCH[6]-}"
                        error_detail=""
                        if ! validate_anchor_status_fragment "$status_fragment" "$allowed_csv" error_detail; then
                            add_finding "$id" "$severity" "$rel_file" "$line_no" "$message $error_detail" "$remediation"
                        fi
                    fi

                    if parse_markdown_cells "$line"; then
                        cells=("${MARKDOWN_CELLS[@]}")

                        if [[ "$in_table" == false ]]; then
                            idx=0
                            table_status_idx=-1
                            for cell in "${cells[@]}"; do
                                if [[ "$cell" =~ $table_header_regex ]]; then
                                    table_status_idx=$idx
                                    break
                                fi
                                idx=$((idx + 1))
                            done
                            if [[ $table_status_idx -ge 0 ]]; then
                                in_table=true
                            fi
                            continue
                        fi

                        if [[ $table_status_idx -lt 0 ]]; then
                            continue
                        fi

                        is_separator=true
                        for cell in "${cells[@]}"; do
                            if [[ ! "$cell" =~ ^:?-{3,}:?$ ]]; then
                                is_separator=false
                                break
                            fi
                        done
                        if [[ "$is_separator" == true ]]; then
                            continue
                        fi

                        if [[ $table_status_idx -ge ${#cells[@]} ]]; then
                            add_finding "$id" "$severity" "$rel_file" "$line_no" "$message Anchor Status column is missing in this table row." "$remediation"
                            continue
                        fi

                        status_cell="${cells[$table_status_idx]}"
                        error_detail=""
                        if ! validate_anchor_status_fragment "$status_cell" "$allowed_csv" error_detail; then
                            add_finding "$id" "$severity" "$rel_file" "$line_no" "$message $error_detail" "$remediation"
                        fi
                        continue
                    fi

                    in_table=false
                    table_status_idx=-1
                done < "$file_path"
            done
            eval "$old_nocasematch"
            ;;

        northbound_controller_required)
            trigger_rel="$(get_param "$params" "trigger_file")"
            [[ -z "$trigger_rel" ]] && trigger_rel="research.md"
            trigger_regex="$(get_param "$params" "trigger_regex")"
            boundary_http_regex="$(get_param "$params" "boundary_http_regex")"
            boundary_forbidden_regex="$(get_param "$params" "boundary_forbidden_regex")"
            entry_controller_regex="$(get_param "$params" "entry_controller_regex")"
            entry_forbidden_regex="$(get_param "$params" "entry_forbidden_regex")"
            sequence_variant_b_regex="$(get_param "$params" "sequence_variant_b_regex")"

            normalized_regex=""
            case_flag="false"
            normalize_regex_for_grep "$trigger_regex" normalized_regex case_flag
            trigger_regex="$normalized_regex"
            normalize_regex_for_grep "$boundary_http_regex" normalized_regex case_flag
            boundary_http_regex="$normalized_regex"
            normalize_regex_for_grep "$boundary_forbidden_regex" normalized_regex case_flag
            boundary_forbidden_regex="$normalized_regex"
            normalize_regex_for_grep "$entry_controller_regex" normalized_regex case_flag
            entry_controller_regex="$normalized_regex"
            normalize_regex_for_grep "$entry_forbidden_regex" normalized_regex case_flag
            entry_forbidden_regex="$normalized_regex"
            normalize_regex_for_grep "$sequence_variant_b_regex" normalized_regex case_flag
            sequence_variant_b_regex="$normalized_regex"

            if [[ -z "$trigger_regex" || -z "$boundary_http_regex" || -z "$boundary_forbidden_regex" || -z "$entry_controller_regex" || -z "$entry_forbidden_regex" || -z "$sequence_variant_b_regex" ]]; then
                add_finding "$id" "$severity" "$glob" 0 "Rule params missing required northbound-controller keys." "Fix rules TSV params for this rule."
                continue
            fi

            trigger_file="$FEATURE_DIR/$trigger_rel"
            if [[ ! -f "$trigger_file" ]]; then
                continue
            fi

            if ! stream_file_for_grep "$trigger_file" | grep -qiE "$trigger_regex"; then
                continue
            fi

            old_nocasematch="$(shopt -p nocasematch || true)"
            shopt -s nocasematch
            boundary_label_regex='^[[:space:]]*([-*][[:space:]]*)?(\*\*)?Boundary[ _-]*Anchor([[:space:]]*\([^)]*\))?(\*\*)?[[:space:]]*:[[:space:]]*(.+)$'
            entry_label_regex='^[[:space:]]*([-*][[:space:]]*)?(\*\*)?Implementation[ _-]*Entry[ _-]*Anchor([[:space:]]*\([^)]*\))?(\*\*)?[[:space:]]*:[[:space:]]*(.+)$'
            boundary_header_regex='^Boundary[ _-]*Anchor$'
            entry_header_regex='^Implementation[ _-]*Entry[ _-]*Anchor$'

            for file_path in "${matched_files[@]}"; do
                rel_file="${file_path#$FEATURE_DIR/}"
                line_no=0
                in_table=false
                boundary_col=-1
                entry_col=-1
                pending_boundary=""
                pending_boundary_line=0
                has_http_boundary=false

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))

                    if [[ "$line" =~ $boundary_label_regex ]]; then
                        if [[ -n "$pending_boundary" ]]; then
                            detail=""
                            if evaluate_northbound_anchor_pair "$pending_boundary" "" "$boundary_http_regex" "$boundary_forbidden_regex" "$entry_controller_regex" "$entry_forbidden_regex" detail; then
                                if ! grep -qiE "$boundary_forbidden_regex" <<< "$pending_boundary"; then
                                    add_finding "$id" "$severity" "$rel_file" "$pending_boundary_line" "$message $detail" "$remediation"
                                fi
                            fi
                        fi
                        pending_boundary="${BASH_REMATCH[5]-}"
                        pending_boundary_line=$line_no
                        if grep -qiE "$boundary_http_regex" <<< "$pending_boundary"; then
                            has_http_boundary=true
                        fi
                        detail=""
                        if evaluate_northbound_anchor_pair "$pending_boundary" "" "$boundary_http_regex" "$boundary_forbidden_regex" "$entry_controller_regex" "$entry_forbidden_regex" detail; then
                            if grep -qiE "$boundary_forbidden_regex" <<< "$pending_boundary"; then
                                add_finding "$id" "$severity" "$rel_file" "$line_no" "$message $detail" "$remediation"
                            fi
                        fi
                        continue
                    fi

                    if [[ "$line" =~ $entry_label_regex && -n "$pending_boundary" ]]; then
                        entry_value="${BASH_REMATCH[5]-}"
                        detail=""
                        if evaluate_northbound_anchor_pair "$pending_boundary" "$entry_value" "$boundary_http_regex" "$boundary_forbidden_regex" "$entry_controller_regex" "$entry_forbidden_regex" detail; then
                            add_finding "$id" "$severity" "$rel_file" "$pending_boundary_line" "$message $detail" "$remediation"
                        fi
                        pending_boundary=""
                        pending_boundary_line=0
                        continue
                    fi

                    if parse_markdown_cells "$line"; then
                        cells=("${MARKDOWN_CELLS[@]}")

                        if [[ "$in_table" == false ]]; then
                            boundary_col=-1
                            entry_col=-1
                            idx=0
                            for cell in "${cells[@]}"; do
                                if [[ "$cell" =~ $boundary_header_regex ]]; then
                                    boundary_col=$idx
                                fi
                                if [[ "$cell" =~ $entry_header_regex ]]; then
                                    entry_col=$idx
                                fi
                                idx=$((idx + 1))
                            done
                            if [[ $boundary_col -ge 0 && $entry_col -ge 0 ]]; then
                                in_table=true
                            fi
                            continue
                        fi

                        is_separator=true
                        for cell in "${cells[@]}"; do
                            if [[ ! "$cell" =~ ^:?-{3,}:?$ ]]; then
                                is_separator=false
                                break
                            fi
                        done
                        if [[ "$is_separator" == true ]]; then
                            continue
                        fi

                        if [[ $boundary_col -ge 0 && $boundary_col -lt ${#cells[@]} ]]; then
                            boundary_value="${cells[$boundary_col]}"
                            if grep -qiE "$boundary_http_regex" <<< "$boundary_value"; then
                                has_http_boundary=true
                            fi
                            entry_value=""
                            if [[ $entry_col -ge 0 && $entry_col -lt ${#cells[@]} ]]; then
                                entry_value="${cells[$entry_col]}"
                            fi
                            detail=""
                            if evaluate_northbound_anchor_pair "$boundary_value" "$entry_value" "$boundary_http_regex" "$boundary_forbidden_regex" "$entry_controller_regex" "$entry_forbidden_regex" detail; then
                                add_finding "$id" "$severity" "$rel_file" "$line_no" "$message $detail" "$remediation"
                            fi
                        fi
                        continue
                    fi

                    in_table=false
                    boundary_col=-1
                    entry_col=-1
                done < "$file_path"

                if [[ -n "$pending_boundary" ]]; then
                    detail=""
                    if evaluate_northbound_anchor_pair "$pending_boundary" "" "$boundary_http_regex" "$boundary_forbidden_regex" "$entry_controller_regex" "$entry_forbidden_regex" detail; then
                        if ! grep -qiE "$boundary_forbidden_regex" <<< "$pending_boundary"; then
                            add_finding "$id" "$severity" "$rel_file" "$pending_boundary_line" "$message $detail" "$remediation"
                        fi
                    fi
                fi

                if [[ "$rel_file" == contracts/* && "$has_http_boundary" == true ]]; then
                    sequence_variant_a_regex='(?i)Sequence[[:space:]]+Variant[[:space:]]+A'
                    if ! stream_file_for_grep "$file_path" | grep -qiE "$sequence_variant_a_regex"; then
                        while IFS= read -r match_line; do
                            [[ -z "$match_line" ]] && continue
                            variant_line="${match_line%%:*}"
                            add_finding "$id" "$severity" "$rel_file" "$variant_line" "$message HTTP boundary contracts must not render Sequence Variant B (Boundary == Entry)." "$remediation"
                        done < <(stream_file_for_grep "$file_path" | grep -niE "$sequence_variant_b_regex" || true)
                    fi
                fi
            done
            eval "$old_nocasematch"
            ;;

        repo_anchor_paths_exist)
            anchor_regex='`?([A-Za-z0-9_./\\-]+\.[A-Za-z0-9_-]+)::([A-Za-z_$][A-Za-z0-9_.$-]*)`?'

            for file_path in "${matched_files[@]}"; do
                rel_file="${file_path#$FEATURE_DIR/}"
                line_no=0

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))
                    remaining="$line"

                    while [[ "$remaining" =~ $anchor_regex ]]; do
                        raw_anchor_path="${BASH_REMATCH[1]}"
                        raw_anchor_token="${BASH_REMATCH[0]}"
                        target_path="$(resolve_anchor_target_path "$REPO_ROOT_FOR_FEATURE" "$raw_anchor_path")"

                        if [[ ! -f "$target_path" ]]; then
                            add_finding "$id" "$severity" "$rel_file" "$line_no" "$message Missing file: $raw_anchor_path" "$remediation"
                        fi

                        remaining="${remaining#*"$raw_anchor_token"}"
                    done
                done < "$file_path"
            done
            ;;

        plan_status_consistency)
            for file_path in "${matched_files[@]}"; do
                rel_file="${file_path#$FEATURE_DIR/}"
                line_no=0
                plan_status=""
                plan_status_line=0
                current_section=""
                in_table=false
                table_status_idx=-1
                stage_statuses=()
                artifact_statuses=()

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))

                    if [[ "$line" =~ ^##[[:space:]]+(.+)$ ]]; then
                        current_section="$(trim "${BASH_REMATCH[1]}")"
                        in_table=false
                        table_status_idx=-1
                        continue
                    fi

                    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*Status:[[:space:]]*(planning-not-started|planning-in-progress|planning-complete)[[:space:]]*$ ]]; then
                        plan_status="${BASH_REMATCH[1]}"
                        plan_status_line=$line_no
                    fi

                    if [[ "$current_section" != "Stage Queue" && "$current_section" != "Artifact Status" ]]; then
                        continue
                    fi

                    if parse_markdown_cells "$line"; then
                        cells=("${MARKDOWN_CELLS[@]}")

                        if [[ "$in_table" == false ]]; then
                            table_status_idx=-1
                            idx=0
                            for cell in "${cells[@]}"; do
                                if [[ "$cell" == "Status" ]]; then
                                    table_status_idx=$idx
                                    break
                                fi
                                idx=$((idx + 1))
                            done
                            if [[ $table_status_idx -ge 0 ]]; then
                                in_table=true
                            fi
                            continue
                        fi

                        is_separator=true
                        for cell in "${cells[@]}"; do
                            if [[ ! "$cell" =~ ^:?-{3,}:?$ ]]; then
                                is_separator=false
                                break
                            fi
                        done
                        if [[ "$is_separator" == true ]]; then
                            continue
                        fi

                        if [[ $table_status_idx -ge 0 && $table_status_idx -lt ${#cells[@]} ]]; then
                            status_value="$(echo "${cells[$table_status_idx]}" | tr '[:upper:]' '[:lower:]')"
                            status_value="$(trim "$status_value")"
                            if [[ "$current_section" == "Stage Queue" ]]; then
                                stage_statuses+=("$status_value")
                            else
                                artifact_statuses+=("$status_value")
                            fi
                        fi
                        continue
                    fi

                    in_table=false
                    table_status_idx=-1
                done < "$file_path"

                if [[ -z "$plan_status" ]]; then
                    add_finding "$id" "$severity" "$rel_file" 0 "$message Missing `Feature Identity -> Status` marker." "$remediation"
                    continue
                fi

                all_stage_pending=true
                all_stage_done=true
                for status_value in "${stage_statuses[@]}"; do
                    [[ "$status_value" != "pending" ]] && all_stage_pending=false
                    [[ "$status_value" != "done" ]] && all_stage_done=false
                done

                artifact_count=${#artifact_statuses[@]}
                all_artifact_done=true
                for status_value in "${artifact_statuses[@]}"; do
                    [[ "$status_value" != "done" ]] && all_artifact_done=false
                done

                if [[ "$plan_status" == "planning-not-started" ]]; then
                    if [[ "$all_stage_pending" == false || $artifact_count -gt 0 ]]; then
                        add_finding "$id" "$severity" "$rel_file" "$plan_status_line" "$message `planning-not-started` is only valid before any stage progress or artifact queue initialization." "$remediation"
                    fi
                    continue
                fi

                if [[ "$plan_status" == "planning-complete" ]]; then
                    if [[ "$all_stage_done" == false || "$all_artifact_done" == false ]]; then
                        add_finding "$id" "$severity" "$rel_file" "$plan_status_line" "$message `planning-complete` requires all stage rows and artifact rows to be `done`." "$remediation"
                    fi
                    continue
                fi

                if [[ "$plan_status" == "planning-in-progress" ]]; then
                    if [[ "$all_stage_pending" == true && $artifact_count -eq 0 ]]; then
                        add_finding "$id" "$severity" "$rel_file" "$plan_status_line" "$message `planning-in-progress` is inconsistent when all stage rows remain `pending` and no artifact queue exists." "$remediation"
                        continue
                    fi

                    if [[ "$all_stage_done" == true && "$all_artifact_done" == true ]]; then
                        add_finding "$id" "$severity" "$rel_file" "$plan_status_line" "$message `planning-in-progress` is inconsistent when all stage rows and artifact rows are already `done`." "$remediation"
                    fi
                fi
            done
            ;;

        binding_projection_stable_only)
            for file_path in "${matched_files[@]}"; do
                rel_file="${file_path#$FEATURE_DIR/}"
                current_section=""
                in_table=false
                line_no=0

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))

                    if [[ "$line" =~ ^##[[:space:]]+(.+)$ ]]; then
                        current_section="$(trim "${BASH_REMATCH[1]}")"
                        in_table=false
                        continue
                    fi

                    if [[ "$current_section" != "Binding Projection Index" ]]; then
                        continue
                    fi

                    if parse_markdown_cells "$line"; then
                        cells=("${MARKDOWN_CELLS[@]}")

                        if [[ "$in_table" == false ]]; then
                            in_table=true
                            for cell in "${cells[@]}"; do
                                case "$cell" in
                                    "Boundary Anchor"|"Implementation Entry Anchor"|"Boundary Anchor Status"|"Implementation Entry Anchor Status"|"Request DTO Anchor"|"Response DTO Anchor"|"Primary Collaborator Anchor"|"State Owner Anchor(s)"|"Repo Anchor"|"Repo Anchor Role"|"Boundary Anchor Strategy Evidence"|"Implementation Entry Anchor Strategy Evidence"|"Lifecycle Ref(s)"|"Invariant Ref(s)"|"Main Pass Anchor"|"Branch/Failure Anchor(s)")
                                        add_finding "$id" "$severity" "$rel_file" "$line_no" "$message" "$remediation"
                                        break
                                        ;;
                                esac
                            done
                            continue
                        fi

                        continue
                    fi

                    in_table=false
                done < "$file_path"
            done
            ;;

        binding_tuple_projection_sync)
            for file_path in "${matched_files[@]}"; do
                rel_file="${file_path#$FEATURE_DIR/}"
                test_matrix_path="$FEATURE_DIR/test-matrix.md"

                if [[ ! -f "$test_matrix_path" ]]; then
                    add_finding "$id" "$severity" "$rel_file" 0 "$message Missing file: test-matrix.md" "$remediation"
                    continue
                fi

                declare -A plan_line=()
                declare -A plan_operation=()
                declare -A plan_if_scope=()
                declare -A plan_tm=()
                declare -A plan_tc=()
                declare -A plan_uif=()
                declare -A plan_udd=()
                declare -A plan_test_scope=()
                declare -A packet_operation=()
                declare -A packet_if_scope=()
                declare -A packet_tm=()
                declare -A packet_tc=()
                declare -A packet_uif=()
                declare -A packet_udd=()
                declare -A packet_test_scope=()
                declare -A packet_line=()

                current_section=""
                in_table=false
                binding_row_idx=-1
                operation_idx=-1
                if_scope_idx=-1
                tm_idx=-1
                tc_idx=-1
                uif_path_idx=-1
                udd_ref_idx=-1
                test_scope_idx=-1
                line_no=0

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))

                    if [[ "$line" =~ ^##[[:space:]]+(.+)$ ]]; then
                        current_section="$(trim "${BASH_REMATCH[1]}")"
                        in_table=false
                        binding_row_idx=-1
                        operation_idx=-1
                        if_scope_idx=-1
                        tm_idx=-1
                        tc_idx=-1
                        uif_path_idx=-1
                        udd_ref_idx=-1
                        test_scope_idx=-1
                        continue
                    fi

                    if [[ "$current_section" != "Binding Projection Index" ]]; then
                        continue
                    fi

                    if ! parse_markdown_cells "$line"; then
                        in_table=false
                        binding_row_idx=-1
                        operation_idx=-1
                        if_scope_idx=-1
                        tm_idx=-1
                        tc_idx=-1
                        uif_path_idx=-1
                        udd_ref_idx=-1
                        test_scope_idx=-1
                        continue
                    fi

                    cells=("${MARKDOWN_CELLS[@]}")

                    if [[ "$in_table" == false ]]; then
                        binding_row_idx=-1
                        operation_idx=-1
                        if_scope_idx=-1
                        tm_idx=-1
                        tc_idx=-1
                        uif_path_idx=-1
                        udd_ref_idx=-1
                        test_scope_idx=-1

                        idx=0
                        for cell in "${cells[@]}"; do
                            case "$cell" in
                                "BindingRowID")
                                    binding_row_idx=$idx
                                    ;;
                                "Operation ID")
                                    operation_idx=$idx
                                    ;;
                                "IF ID / IF Scope")
                                    if_scope_idx=$idx
                                    ;;
                                "TM ID")
                                    tm_idx=$idx
                                    ;;
                                "TC IDs")
                                    tc_idx=$idx
                                    ;;
                                "UIF Path Ref(s)")
                                    uif_path_idx=$idx
                                    ;;
                                "UDD Ref(s)")
                                    udd_ref_idx=$idx
                                    ;;
                                "Test Scope")
                                    test_scope_idx=$idx
                                    ;;
                            esac
                            idx=$((idx + 1))
                        done

                        if [[ $binding_row_idx -ge 0 ]]; then
                            in_table=true
                        fi
                        continue
                    fi

                    is_separator=true
                    for cell in "${cells[@]}"; do
                        if [[ ! "$cell" =~ ^:?-{3,}:?$ ]]; then
                            is_separator=false
                            break
                        fi
                    done
                    if [[ "$is_separator" == true ]]; then
                        continue
                    fi

                    if [[ $binding_row_idx -lt 0 || $binding_row_idx -ge ${#cells[@]} ]]; then
                        continue
                    fi

                    binding_id="$(normalize_markdown_scalar "${cells[$binding_row_idx]}")"
                    [[ -z "$binding_id" ]] && continue

                    plan_line["$binding_id"]=$line_no
                    if [[ $operation_idx -ge 0 && $operation_idx -lt ${#cells[@]} ]]; then
                        plan_operation["$binding_id"]="$(normalize_markdown_scalar "${cells[$operation_idx]}")"
                    fi
                    if [[ $if_scope_idx -ge 0 && $if_scope_idx -lt ${#cells[@]} ]]; then
                        plan_if_scope["$binding_id"]="$(normalize_markdown_scalar "${cells[$if_scope_idx]}")"
                    fi
                    if [[ $tm_idx -ge 0 && $tm_idx -lt ${#cells[@]} ]]; then
                        plan_tm["$binding_id"]="$(normalize_markdown_scalar "${cells[$tm_idx]}")"
                    fi
                    if [[ $tc_idx -ge 0 && $tc_idx -lt ${#cells[@]} ]]; then
                        plan_tc["$binding_id"]="$(normalize_markdown_list_cell "${cells[$tc_idx]}")"
                    fi
                    if [[ $uif_path_idx -ge 0 && $uif_path_idx -lt ${#cells[@]} ]]; then
                        plan_uif["$binding_id"]="$(normalize_markdown_list_cell "${cells[$uif_path_idx]}")"
                    fi
                    if [[ $udd_ref_idx -ge 0 && $udd_ref_idx -lt ${#cells[@]} ]]; then
                        plan_udd["$binding_id"]="$(normalize_markdown_list_cell "${cells[$udd_ref_idx]}")"
                    fi
                    if [[ $test_scope_idx -ge 0 && $test_scope_idx -lt ${#cells[@]} ]]; then
                        plan_test_scope["$binding_id"]="$(normalize_markdown_scalar "${cells[$test_scope_idx]}")"
                    fi
                done < "$file_path"

                current_section=""
                in_table=false
                binding_row_idx=-1
                operation_idx=-1
                if_scope_idx=-1
                tm_idx=-1
                tc_idx=-1
                uif_path_idx=-1
                udd_ref_idx=-1
                test_scope_idx=-1
                line_no=0

                while IFS= read -r line || [[ -n "$line" ]]; do
                    line_no=$((line_no + 1))

                    if [[ "$line" =~ ^##[[:space:]]+(.+)$ ]]; then
                        current_section="$(trim "${BASH_REMATCH[1]}")"
                        in_table=false
                        binding_row_idx=-1
                        operation_idx=-1
                        if_scope_idx=-1
                        tm_idx=-1
                        tc_idx=-1
                        uif_path_idx=-1
                        udd_ref_idx=-1
                        test_scope_idx=-1
                        continue
                    fi

                    if [[ "$current_section" != "Binding Contract Packets" ]]; then
                        continue
                    fi

                    if ! parse_markdown_cells "$line"; then
                        in_table=false
                        binding_row_idx=-1
                        operation_idx=-1
                        if_scope_idx=-1
                        tm_idx=-1
                        tc_idx=-1
                        uif_path_idx=-1
                        udd_ref_idx=-1
                        test_scope_idx=-1
                        continue
                    fi

                    cells=("${MARKDOWN_CELLS[@]}")

                    if [[ "$in_table" == false ]]; then
                        binding_row_idx=-1
                        operation_idx=-1
                        if_scope_idx=-1
                        tm_idx=-1
                        tc_idx=-1
                        uif_path_idx=-1
                        udd_ref_idx=-1
                        test_scope_idx=-1

                        idx=0
                        for cell in "${cells[@]}"; do
                            case "$cell" in
                                "BindingRowID")
                                    binding_row_idx=$idx
                                    ;;
                                "Operation ID")
                                    operation_idx=$idx
                                    ;;
                                "IF Scope")
                                    if_scope_idx=$idx
                                    ;;
                                "TM ID")
                                    tm_idx=$idx
                                    ;;
                                "TC IDs")
                                    tc_idx=$idx
                                    ;;
                                "UIF Path Ref(s)")
                                    uif_path_idx=$idx
                                    ;;
                                "UDD Ref(s)")
                                    udd_ref_idx=$idx
                                    ;;
                                "Test Scope")
                                    test_scope_idx=$idx
                                    ;;
                            esac
                            idx=$((idx + 1))
                        done
                        if [[ $binding_row_idx -ge 0 ]]; then
                            in_table=true
                        fi
                        continue
                    fi

                    is_separator=true
                    for cell in "${cells[@]}"; do
                        if [[ ! "$cell" =~ ^:?-{3,}:?$ ]]; then
                            is_separator=false
                            break
                        fi
                    done
                    if [[ "$is_separator" == true ]]; then
                        continue
                    fi

                    if [[ $binding_row_idx -lt 0 || $binding_row_idx -ge ${#cells[@]} ]]; then
                        continue
                    fi

                    binding_id="$(normalize_markdown_scalar "${cells[$binding_row_idx]}")"
                    [[ -z "$binding_id" ]] && continue

                    packet_line["$binding_id"]=$line_no
                    if [[ $operation_idx -ge 0 && $operation_idx -lt ${#cells[@]} ]]; then
                        packet_operation["$binding_id"]="$(normalize_markdown_scalar "${cells[$operation_idx]}")"
                    fi
                    if [[ $if_scope_idx -ge 0 && $if_scope_idx -lt ${#cells[@]} ]]; then
                        packet_if_scope["$binding_id"]="$(normalize_markdown_scalar "${cells[$if_scope_idx]}")"
                    fi
                    if [[ $tm_idx -ge 0 && $tm_idx -lt ${#cells[@]} ]]; then
                        packet_tm["$binding_id"]="$(normalize_markdown_scalar "${cells[$tm_idx]}")"
                    fi
                    if [[ $tc_idx -ge 0 && $tc_idx -lt ${#cells[@]} ]]; then
                        packet_tc["$binding_id"]="$(normalize_markdown_list_cell "${cells[$tc_idx]}")"
                    fi
                    if [[ $uif_path_idx -ge 0 && $uif_path_idx -lt ${#cells[@]} ]]; then
                        packet_uif["$binding_id"]="$(normalize_markdown_list_cell "${cells[$uif_path_idx]}")"
                    fi
                    if [[ $udd_ref_idx -ge 0 && $udd_ref_idx -lt ${#cells[@]} ]]; then
                        packet_udd["$binding_id"]="$(normalize_markdown_list_cell "${cells[$udd_ref_idx]}")"
                    fi
                    if [[ $test_scope_idx -ge 0 && $test_scope_idx -lt ${#cells[@]} ]]; then
                        packet_test_scope["$binding_id"]="$(normalize_markdown_scalar "${cells[$test_scope_idx]}")"
                    fi
                done < "$test_matrix_path"

                for binding_id in "${!plan_line[@]}"; do
                    if [[ -z "${packet_line[$binding_id]:-}" ]]; then
                        add_finding "$id" "$severity" "$rel_file" "${plan_line[$binding_id]}" "$message BindingRowID $binding_id is present in `Binding Projection Index` but missing from `test-matrix.md` `Binding Contract Packets`." "$remediation"
                        continue
                    fi

                    if [[ "${plan_operation[$binding_id]:-}" != "${packet_operation[$binding_id]:-}" || "${plan_if_scope[$binding_id]:-}" != "${packet_if_scope[$binding_id]:-}" || "${plan_tm[$binding_id]:-}" != "${packet_tm[$binding_id]:-}" || "${plan_tc[$binding_id]:-}" != "${packet_tc[$binding_id]:-}" || "${plan_uif[$binding_id]:-}" != "${packet_uif[$binding_id]:-}" || "${plan_udd[$binding_id]:-}" != "${packet_udd[$binding_id]:-}" || "${plan_test_scope[$binding_id]:-}" != "${packet_test_scope[$binding_id]:-}" ]]; then
                        add_finding "$id" "$severity" "$rel_file" "${plan_line[$binding_id]}" "$message BindingRowID $binding_id differs from `test-matrix.md` `Binding Contract Packets` for minimal projection fields." "$remediation"
                    fi

                done
            done
            ;;

        *)
            add_finding "$id" "$severity" "$glob" 0 "Unsupported rule kind: $kind" "Use one of: file_regex_forbidden, file_regex_required_any, component_symbols_exist, anchor_status_allowed_values, northbound_controller_required, repo_anchor_paths_exist, plan_status_consistency, binding_projection_stable_only, binding_tuple_projection_sync."
            ;;
    esac

done < "$RULES_PATH"

if [[ ${#findings_json_items[@]} -eq 0 ]]; then
    findings_json='[]'
else
    findings_json="[$(IFS=,; echo "${findings_json_items[*]}")]"
fi

severity_keys=(CRITICAL HIGH MEDIUM LOW INFO)
severity_json_parts=()
for key in "${severity_keys[@]}"; do
    severity_json_parts+=("\"$key\":${severity_counts[$key]:-0}")
done
findings_by_severity_json="{$(IFS=,; echo "${severity_json_parts[*]}")}"

if $JSON_MODE; then
    printf '{"feature_dir":"%s","rules_total":%d,"rules_evaluated":%d,"findings_total":%d,"findings_by_severity":%s,"findings":%s}\n' \
        "$(json_escape "$FEATURE_DIR")" \
        "$rules_total" \
        "$rules_evaluated" \
        "$findings_total" \
        "$findings_by_severity_json" \
        "$findings_json"
else
    echo "feature_dir: $FEATURE_DIR"
    echo "rules_total: $rules_total"
    echo "rules_evaluated: $rules_evaluated"
    echo "findings_total: $findings_total"
    echo "findings_by_severity: $findings_by_severity_json"
    if [[ "$findings_total" -gt 0 ]]; then
        echo "findings:"
        for item in "${findings_json_items[@]}"; do
            echo "  $item"
        done
    else
        echo "findings: []"
    fi
fi
