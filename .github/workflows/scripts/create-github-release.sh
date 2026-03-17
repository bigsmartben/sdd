#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files.
# Usage: .github/workflows/scripts/create-github-release.sh <version>
# Enforces full template coverage across all AGENT_CONFIG keys and both script variants.

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
VERSION_NO_V=${VERSION#v}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_KEYS_SCRIPT="$SCRIPT_DIR/list-agent-config-keys.py"

shopt -s nullglob
TEMPLATE_ZIPS=(.genreleases/spec-kit-template-*-${VERSION}.zip)
PYTHON_DIST=(dist/*.whl dist/*.tar.gz)
shopt -u nullglob

if [[ ${#TEMPLATE_ZIPS[@]} -eq 0 ]]; then
  echo "No template archives found for ${VERSION} under .genreleases/" >&2
  exit 1
fi

if [[ ! -f "$AGENT_KEYS_SCRIPT" ]]; then
  echo "Missing helper script: $AGENT_KEYS_SCRIPT" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for release asset gate checks" >&2
  exit 1
fi

mapfile -t RELEASE_AGENTS < <(python3 "$AGENT_KEYS_SCRIPT")
if [[ ${#RELEASE_AGENTS[@]} -eq 0 ]]; then
  echo "AGENT_CONFIG key list is empty; refusing to create release" >&2
  exit 1
fi

missing_assets=()
for agent in "${RELEASE_AGENTS[@]}"; do
  for script in sh ps; do
    expected=".genreleases/spec-kit-template-${agent}-${script}-${VERSION}.zip"
    if [[ ! -f "$expected" ]]; then
      missing_assets+=("$expected")
    fi
  done
done

if [[ ${#missing_assets[@]} -ne 0 ]]; then
  echo "Release gate failed: missing template archives (${#missing_assets[@]}):" >&2
  printf '  - %s\n' "${missing_assets[@]}" >&2
  exit 1
fi

expected_total=$(( ${#RELEASE_AGENTS[@]} * 2 ))
if [[ ${#TEMPLATE_ZIPS[@]} -ne "$expected_total" ]]; then
  echo "Release gate failed: template archive count mismatch for ${VERSION}. expected=$expected_total actual=${#TEMPLATE_ZIPS[@]}" >&2
  exit 1
fi

if [[ ${#PYTHON_DIST[@]} -eq 0 ]]; then
  echo "No Python distribution artifacts found under dist/" >&2
  exit 1
fi

gh release create "$VERSION" \
  "${TEMPLATE_ZIPS[@]}" \
  "${PYTHON_DIST[@]}" \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
