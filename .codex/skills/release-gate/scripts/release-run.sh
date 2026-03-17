#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  release-run.sh <version-with-v-prefix> [--publish]

Examples:
  release-run.sh v2.0.17
  release-run.sh v2.0.17 --publish
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

VERSION="$1"
PUBLISH=0
if [[ $# -eq 2 ]]; then
  if [[ "$2" != "--publish" ]]; then
    usage
    exit 1
  fi
  PUBLISH=1
fi

if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: version must look like v0.0.0" >&2
  exit 1
fi

require_tool() {
  local tool="$1"
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: required tool missing: $tool" >&2
    exit 1
  fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "Error: failed to resolve repository root from $SCRIPT_DIR" >&2
  exit 1
fi

RELEASE_SCRIPTS_DIR="$REPO_ROOT/.github/workflows/scripts"
PACKAGE_SCRIPT="$RELEASE_SCRIPTS_DIR/create-release-packages.sh"
NOTES_SCRIPT="$RELEASE_SCRIPTS_DIR/generate-release-notes.sh"
PUBLISH_SCRIPT="$RELEASE_SCRIPTS_DIR/create-github-release.sh"
AGENT_KEYS_SCRIPT="$RELEASE_SCRIPTS_DIR/list-agent-config-keys.py"

for path in \
  "$PACKAGE_SCRIPT" \
  "$NOTES_SCRIPT" \
  "$PUBLISH_SCRIPT" \
  "$AGENT_KEYS_SCRIPT"
do
  if [[ ! -f "$path" ]]; then
    echo "Error: required script missing: $path" >&2
    exit 1
  fi
done

require_tool bash
require_tool git
require_tool python3
require_tool uv
require_tool zip
require_tool find
require_tool sed
require_tool awk
if [[ $PUBLISH -eq 1 ]]; then
  require_tool gh
fi

cd "$REPO_ROOT"

echo "== Release Runner =="
echo "Repo   : $REPO_ROOT"
echo "Version: $VERSION"
echo "Mode   : $([[ $PUBLISH -eq 1 ]] && echo publish || echo preflight)"

echo
echo "[1/5] Build template archives"
bash "$PACKAGE_SCRIPT" "$VERSION"

echo
echo "[2/5] Build Python distributions"
uv build

echo
echo "[3/5] Generate release notes"
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  PREVIOUS_TAG="$(git describe --tags --abbrev=0 "$VERSION^" 2>/dev/null || echo "v0.0.0")"
else
  PREVIOUS_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")"
fi
bash "$NOTES_SCRIPT" "$VERSION" "$PREVIOUS_TAG"

echo
echo "[4/5] Enforce full template coverage gate (all agents x sh/ps)"
mapfile -t RELEASE_AGENTS < <(python3 "$AGENT_KEYS_SCRIPT")
if [[ ${#RELEASE_AGENTS[@]} -eq 0 ]]; then
  echo "Error: AGENT_CONFIG key list is empty" >&2
  exit 1
fi

MISSING=()
for agent in "${RELEASE_AGENTS[@]}"; do
  for script in sh ps; do
    expected="$REPO_ROOT/.genreleases/spec-kit-template-${agent}-${script}-${VERSION}.zip"
    if [[ ! -f "$expected" ]]; then
      MISSING+=("$expected")
    fi
  done
done

if [[ ${#MISSING[@]} -ne 0 ]]; then
  echo "Error: release gate failed; missing template archives (${#MISSING[@]}):" >&2
  printf '  - %s\n' "${MISSING[@]}" >&2
  exit 1
fi

shopt -s nullglob
TEMPLATE_ZIPS=("$REPO_ROOT"/.genreleases/spec-kit-template-*-"${VERSION}".zip)
PYTHON_DIST=("$REPO_ROOT"/dist/*.whl "$REPO_ROOT"/dist/*.tar.gz)
shopt -u nullglob

EXPECTED_TOTAL=$(( ${#RELEASE_AGENTS[@]} * 2 ))
if [[ ${#TEMPLATE_ZIPS[@]} -ne "$EXPECTED_TOTAL" ]]; then
  echo "Error: template archive count mismatch. expected=$EXPECTED_TOTAL actual=${#TEMPLATE_ZIPS[@]}" >&2
  exit 1
fi

if [[ ${#PYTHON_DIST[@]} -eq 0 ]]; then
  echo "Error: no Python dist artifacts found under $REPO_ROOT/dist" >&2
  exit 1
fi

echo "Gate check passed: templates=${#TEMPLATE_ZIPS[@]} dist=${#PYTHON_DIST[@]}"

echo
if [[ $PUBLISH -eq 1 ]]; then
  echo "[5/5] Publish GitHub release"
  bash "$PUBLISH_SCRIPT" "$VERSION"
  echo "Release published: $VERSION"
else
  echo "[5/5] Preflight complete (publish skipped)"
  echo "Run with --publish to create the GitHub release."
fi

