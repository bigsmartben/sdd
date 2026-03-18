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
  --feature-dir <abs-path>   Absolute path to feature directory (e.g. /repo/specs/001-feature)
  --rules <abs-path>         Absolute path to rules TSV catalog
  --json                     Output machine-readable JSON
  --help                     Show this help message

Supported rule kinds:
  - file_regex_forbidden
  - file_regex_required_any
  - component_symbols_exist
  - anchor_status_allowed_values
  - northbound_controller_required
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

trim() {
    local value="$1"
    # shellcheck disable=SC2001
    value="$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    printf '%s' "$value"
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

    printf -v "$__out_regex_ref" '%s' "$regex"
    printf -v "$__out_case_insensitive_ref" '%s' "$case_insensitive"
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

while IFS=$'\t' read -r id enabled severity scope glob kind params message remediation _; do
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
                    done < <(grep -niE "$normalized_regex" "$file_path" || true)
                else
                    while IFS= read -r match_line; do
                        [[ -z "$match_line" ]] && continue
                        line_no="${match_line%%:*}"
                        rel_file="${file_path#$FEATURE_DIR/}"
                        add_finding "$id" "$severity" "$rel_file" "$line_no" "$message" "$remediation"
                    done < <(grep -nE "$normalized_regex" "$file_path" || true)
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
                    if grep -qiE "$normalized_regex" "$file_path"; then
                        found_any=true
                        break
                    fi
                else
                    if grep -qE "$normalized_regex" "$file_path"; then
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
                if ! grep -Fq -- "$symbol_trimmed" "$target_file"; then
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

                    if [[ "$line" =~ ^[[:space:]]*\|.*\|[[:space:]]*$ ]]; then
                        line_trimmed="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
                        content="${line_trimmed#|}"
                        content="${content%|}"
                        IFS='|' read -r -a raw_cells <<< "$content"
                        cells=()
                        for cell in "${raw_cells[@]}"; do
                            cells+=("$(trim "$cell")")
                        done

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

            if ! grep -qiE "$trigger_regex" "$trigger_file"; then
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

                    if [[ "$line" =~ ^[[:space:]]*\|.*\|[[:space:]]*$ ]]; then
                        line_trimmed="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
                        content="${line_trimmed#|}"
                        content="${content%|}"
                        IFS='|' read -r -a raw_cells <<< "$content"
                        cells=()
                        for cell in "${raw_cells[@]}"; do
                            cells+=("$(trim "$cell")")
                        done

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
                            if [[ $boundary_col -ge 0 || $entry_col -ge 0 ]]; then
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
                    while IFS= read -r match_line; do
                        [[ -z "$match_line" ]] && continue
                        variant_line="${match_line%%:*}"
                        add_finding "$id" "$severity" "$rel_file" "$variant_line" "$message HTTP boundary contracts must not render Sequence Variant B (Boundary == Entry)." "$remediation"
                    done < <(grep -niE "$sequence_variant_b_regex" "$file_path" || true)
                fi
            done
            eval "$old_nocasematch"
            ;;

        *)
            add_finding "$id" "$severity" "$glob" 0 "Unsupported rule kind: $kind" "Use one of: file_regex_forbidden, file_regex_required_any, component_symbols_exist, anchor_status_allowed_values, northbound_controller_required."
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
