#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of AGENT_CONFIG keys from src/specify_cli/__init__.py (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version-with-v-prefix>" >&2
  exit 1
fi

NEW_VERSION="$1"
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v0.0.0" >&2
  exit 1
fi

echo "Building release packages for $NEW_VERSION"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_KEYS_SCRIPT="$SCRIPT_DIR/list-agent-config-keys.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"
USE_UV_PYTHON="${USE_UV_PYTHON:-0}"

run_python() {
  if [[ "$USE_UV_PYTHON" == "1" ]]; then
    uv run python "$@"
  else
    "$PYTHON_BIN" "$@"
  fi
}

GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "$GENRELEASES_DIR"/* || true

if [[ -d templates/commands ]]; then
  TEMPLATE_COMMAND_COUNT=$(find templates/commands -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')
else
  TEMPLATE_COMMAND_COUNT=0
fi

if [[ "$TEMPLATE_COMMAND_COUNT" -eq 0 ]]; then
  echo "Error: no command templates found under templates/commands" >&2
  exit 1
fi

rewrite_paths() {
  sed -E \
    -e 's@(/?)memory/@.specify/memory/@g' \
    -e 's@(/?)scripts/@.specify/scripts/@g' \
    -e 's@(/?)templates/@.specify/templates/@g' \
    -e 's@\.specify\.specify/@.specify/@g'
}

validate_generated_command_files() {
  local output_dir=$1 ext=$2 agent=$3
  local generated_count
  generated_count=$(find "$output_dir" -maxdepth 1 -type f -name "sdd.*.${ext}" | wc -l | tr -d ' ')

  if [[ "$generated_count" -ne "$TEMPLATE_COMMAND_COUNT" ]]; then
    echo "Error: generated command count mismatch for $agent ($ext). expected=$TEMPLATE_COMMAND_COUNT actual=$generated_count dir=$output_dir" >&2
    exit 1
  fi
}

validate_copilot_prompt_files() {
  local agents_dir=$1 prompts_dir=$2
  local agent_count prompt_count
  agent_count=$(find "$agents_dir" -maxdepth 1 -type f -name 'sdd.*.agent.md' | wc -l | tr -d ' ')
  prompt_count=$(find "$prompts_dir" -maxdepth 1 -type f -name 'sdd.*.prompt.md' | wc -l | tr -d ' ')

  if [[ "$agent_count" -ne "$prompt_count" ]]; then
    echo "Error: generated Copilot prompt count mismatch. expected=$agent_count actual=$prompt_count prompts_dir=$prompts_dir" >&2
    exit 1
  fi
}

validate_generated_kimi_skills() {
  local skills_dir=$1
  local skill_count
  skill_count=$(find "$skills_dir" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | wc -l | tr -d ' ')

  if [[ "$skill_count" -ne "$TEMPLATE_COMMAND_COUNT" ]]; then
    echo "Error: generated Kimi skill count mismatch. expected=$TEMPLATE_COMMAND_COUNT actual=$skill_count dir=$skills_dir" >&2
    exit 1
  fi
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4 script_variant=$5
  mkdir -p "$output_dir"

  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue

    local name description script_command agent_script_command body file_content
    name=$(basename "$template" .md)
    file_content=$(tr -d '\r' < "$template")

    description=$(awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' <<< "$file_content")
    script_command=$(awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}' <<< "$file_content")

    if [[ -z $script_command ]]; then
      if [[ $file_content == *"{SCRIPT}"* ]]; then
        echo "Warning: no script command found for $script_variant in $template" >&2
      fi
      script_command="(Missing script command for $script_variant)"
    fi

    agent_script_command=$(awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ' <<< "$file_content")

    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi

    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')

    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)

    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        {
          echo "description = \"$description\""
          echo
          echo "prompt = \"\"\""
          echo "$body"
          echo "\"\"\""
        } > "$output_dir/sdd.$name.$ext"
        ;;
      md|agent.md)
        echo "$body" > "$output_dir/sdd.$name.$ext"
        ;;
      *)
        echo "Unsupported extension '$ext'" >&2
        exit 1
        ;;
    esac
  done

  validate_generated_command_files "$output_dir" "$ext" "$agent"
}

generate_copilot_prompts() {
  local agents_dir=$1 prompts_dir=$2
  mkdir -p "$prompts_dir"

  for agent_file in "$agents_dir"/sdd.*.agent.md; do
    [[ -f "$agent_file" ]] || continue

    local basename prompt_file
    basename=$(basename "$agent_file" .agent.md)
    prompt_file="$prompts_dir/${basename}.prompt.md"

    cat > "$prompt_file" <<EOF
---
agent: ${basename}
---
EOF
  done

  validate_copilot_prompt_files "$agents_dir" "$prompts_dir"
}

# Create Kimi Code skills in .kimi/skills/<name>/SKILL.md format.
create_kimi_skills() {
  local skills_dir=$1 script_variant=$2

  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue

    local name skill_name skill_dir file_content description script_command
    local agent_script_command body template_body

    name=$(basename "$template" .md)
    skill_name="sdd.${name}"
    skill_dir="${skills_dir}/${skill_name}"
    mkdir -p "$skill_dir"

    file_content=$(tr -d '\r' < "$template")

    description=$(awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' <<< "$file_content")
    [[ -z $description ]] && description="Spec Kit: ${name} workflow"

    script_command=$(awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}' <<< "$file_content")
    if [[ -z $script_command ]]; then
      if [[ $file_content == *"{SCRIPT}"* ]]; then
        echo "Warning: no script command found for $script_variant in $template" >&2
      fi
      script_command="(Missing script command for $script_variant)"
    fi

    agent_script_command=$(awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ' <<< "$file_content")

    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi

    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')

    body=$(printf '%s\n' "$body" | sed 's/{ARGS}/\$ARGUMENTS/g' | sed 's/__AGENT__/kimi/g' | rewrite_paths)
    template_body=$(printf '%s\n' "$body" | awk '/^---/{p++; if(p==2){found=1; next}} found')

    {
      printf -- '---\n'
      printf 'name: "%s"\n' "$skill_name"
      printf 'description: "%s"\n' "$description"
      printf -- '---\n\n'
      printf '%s\n' "$template_body"
    } > "$skill_dir/SKILL.md"
  done

  validate_generated_kimi_skills "$skills_dir"
}

build_variant() {
  local agent=$1 script=$2
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-${script}"

  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"

  local spec_dir="$base_dir/.specify"
  mkdir -p "$spec_dir"

  [[ -d memory ]] && cp -r memory "$spec_dir/"

  if [[ -d scripts ]]; then
    mkdir -p "$spec_dir/scripts"
    case $script in
      sh)
        [[ -d scripts/bash ]] && cp -r scripts/bash "$spec_dir/scripts/"
        ;;
      ps)
        [[ -d scripts/powershell ]] && cp -r scripts/powershell "$spec_dir/scripts/"
        ;;
    esac
    find scripts -maxdepth 1 -type f -exec cp {} "$spec_dir/scripts/" \; 2>/dev/null || true
  fi

  if [[ -d templates ]]; then
    mkdir -p "$spec_dir/templates"
    find templates -type f -not -path "templates/commands/*" -not -name "vscode-settings.json" -exec cp --parents {} "$spec_dir"/ \;
  fi

  if [[ -f rules/planning-lint-rules.tsv ]]; then
    mkdir -p "$spec_dir/rules"
    cp rules/planning-lint-rules.tsv "$spec_dir/rules/planning-lint-rules.tsv"
  fi

  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" "$script"
      ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands" "$script"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md"
      ;;
    copilot)
      mkdir -p "$base_dir/.github/agents"
      generate_commands copilot agent.md "\$ARGUMENTS" "$base_dir/.github/agents" "$script"
      generate_copilot_prompts "$base_dir/.github/agents" "$base_dir/.github/prompts"
      mkdir -p "$base_dir/.vscode"
      [[ -f templates/vscode-settings.json ]] && cp templates/vscode-settings.json "$base_dir/.vscode/settings.json"
      ;;
    cursor-agent)
      mkdir -p "$base_dir/.cursor/commands"
      generate_commands cursor-agent md "\$ARGUMENTS" "$base_dir/.cursor/commands" "$script"
      ;;
    cline)
      mkdir -p "$base_dir/.clinerules/workflows"
      generate_commands cline md "\$ARGUMENTS" "$base_dir/.clinerules/workflows" "$script"
      ;;
    qwen)
      mkdir -p "$base_dir/.qwen/commands"
      generate_commands qwen toml "{{args}}" "$base_dir/.qwen/commands" "$script"
      [[ -f agent_templates/qwen/QWEN.md ]] && cp agent_templates/qwen/QWEN.md "$base_dir/QWEN.md"
      ;;
    opencode)
      mkdir -p "$base_dir/.opencode/command"
      generate_commands opencode md "\$ARGUMENTS" "$base_dir/.opencode/command" "$script"
      ;;
    windsurf)
      mkdir -p "$base_dir/.windsurf/workflows"
      generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script"
      ;;
    codex)
      mkdir -p "$base_dir/.codex/prompts"
      generate_commands codex md "\$ARGUMENTS" "$base_dir/.codex/prompts" "$script"
      ;;
    kilocode)
      mkdir -p "$base_dir/.kilocode/rules"
      generate_commands kilocode md "\$ARGUMENTS" "$base_dir/.kilocode/rules" "$script"
      ;;
    auggie)
      mkdir -p "$base_dir/.augment/rules"
      generate_commands auggie md "\$ARGUMENTS" "$base_dir/.augment/rules" "$script"
      ;;
    roo)
      mkdir -p "$base_dir/.roo/commands"
      generate_commands roo md "\$ARGUMENTS" "$base_dir/.roo/commands" "$script"
      ;;
    codebuddy)
      mkdir -p "$base_dir/.codebuddy/commands"
      generate_commands codebuddy md "\$ARGUMENTS" "$base_dir/.codebuddy/commands" "$script"
      ;;
    qodercli)
      mkdir -p "$base_dir/.qoder/commands"
      generate_commands qodercli md "\$ARGUMENTS" "$base_dir/.qoder/commands" "$script"
      ;;
    amp)
      mkdir -p "$base_dir/.agents/commands"
      generate_commands amp md "\$ARGUMENTS" "$base_dir/.agents/commands" "$script"
      ;;
    shai)
      mkdir -p "$base_dir/.shai/commands"
      generate_commands shai md "\$ARGUMENTS" "$base_dir/.shai/commands" "$script"
      ;;
    tabnine)
      mkdir -p "$base_dir/.tabnine/agent/commands"
      generate_commands tabnine toml "{{args}}" "$base_dir/.tabnine/agent/commands" "$script"
      [[ -f agent_templates/tabnine/TABNINE.md ]] && cp agent_templates/tabnine/TABNINE.md "$base_dir/TABNINE.md"
      ;;
    kiro-cli)
      mkdir -p "$base_dir/.kiro/prompts"
      generate_commands kiro-cli md "\$ARGUMENTS" "$base_dir/.kiro/prompts" "$script"
      ;;
    agy)
      mkdir -p "$base_dir/.agent/workflows"
      generate_commands agy md "\$ARGUMENTS" "$base_dir/.agent/workflows" "$script"
      ;;
    bob)
      mkdir -p "$base_dir/.bob/commands"
      generate_commands bob md "\$ARGUMENTS" "$base_dir/.bob/commands" "$script"
      ;;
    vibe)
      mkdir -p "$base_dir/.vibe/prompts"
      generate_commands vibe md "\$ARGUMENTS" "$base_dir/.vibe/prompts" "$script"
      ;;
    kimi)
      mkdir -p "$base_dir/.kimi/skills"
      create_kimi_skills "$base_dir/.kimi/skills" "$script"
      ;;
    generic)
      mkdir -p "$base_dir/.sdd/commands"
      generate_commands generic md "\$ARGUMENTS" "$base_dir/.sdd/commands" "$script"
      ;;
    *)
      echo "Unsupported agent '$agent'" >&2
      exit 1
      ;;
  esac

  (
    cd "$base_dir"
    if command -v zip >/dev/null 2>&1; then
      zip -r "../spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip" .
    elif command -v tar >/dev/null 2>&1; then
      tar -a -cf "../spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip" .
    else
      echo "Error: neither zip nor tar is available to create release archives" >&2
      exit 1
    fi
  )
  echo "Created $GENRELEASES_DIR/spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Compatibility seed list for tooling/tests that parse ALL_AGENTS directly.
# Runtime agent selection is refreshed from AGENT_CONFIG via load_all_agents().
ALL_AGENTS=(copilot claude gemini cursor-agent cline qwen opencode codex windsurf kilocode auggie codebuddy qodercli roo kiro-cli amp shai tabnine agy bob vibe kimi generic)

load_all_agents() {
  local helper_output

  if [[ ! -f "$AGENT_KEYS_SCRIPT" ]]; then
    echo "Error: agent key helper not found: $AGENT_KEYS_SCRIPT" >&2
    exit 1
  fi

  if ! run_python -c "import sys" >/dev/null 2>&1; then
    echo "Error: python3 is required to load AGENT_CONFIG keys (PYTHON_BIN=$PYTHON_BIN, USE_UV_PYTHON=$USE_UV_PYTHON)" >&2
    exit 1
  fi

  if ! helper_output=$(run_python "$AGENT_KEYS_SCRIPT" | tr -d '\r'); then
    echo "Error: failed to load AGENT_CONFIG keys from helper script: $AGENT_KEYS_SCRIPT" >&2
    exit 1
  fi

  mapfile -t ALL_AGENTS < <(printf '%s\n' "$helper_output" | awk 'NF')
  if [[ ${#ALL_AGENTS[@]} -eq 0 ]]; then
    echo "Error: AGENT_CONFIG key list is empty; refusing to continue" >&2
    exit 1
  fi
}

load_all_agents
ALL_SCRIPTS=(sh ps)

norm_list() {
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?"\n":"") $i);out=1}}}END{printf("\n")}'
}

validate_subset() {
  local type=$1
  shift
  local -n allowed=$1
  shift
  local items=("$@")
  local invalid=0

  for it in "${items[@]}"; do
    local found=0
    for a in "${allowed[@]}"; do
      [[ $it == "$a" ]] && { found=1; break; }
    done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: ${allowed[*]})" >&2
      invalid=1
    fi
  done

  return $invalid
}

if [[ -n ${AGENTS:-} ]]; then
  mapfile -t AGENT_LIST < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent ALL_AGENTS "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

if [[ -n ${SCRIPTS:-} ]]; then
  mapfile -t SCRIPT_LIST < <(printf '%s' "$SCRIPTS" | norm_list)
  validate_subset script ALL_SCRIPTS "${SCRIPT_LIST[@]}" || exit 1
else
  SCRIPT_LIST=("${ALL_SCRIPTS[@]}")
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Scripts: ${SCRIPT_LIST[*]}"

for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/spec-kit-template-*-"${NEW_VERSION}".zip
