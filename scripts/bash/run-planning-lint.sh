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
EOF
}

error() {
    echo "ERROR: $*" >&2
}

is_abs_path() {
    [[ "$1" == /* ]]
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

        *)
            add_finding "$id" "$severity" "$glob" 0 "Unsupported rule kind: $kind" "Use one of: file_regex_forbidden, file_regex_required_any, component_symbols_exist."
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
