#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files.
# Usage: .github/workflows/scripts/create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
VERSION_NO_V=${VERSION#v}

shopt -s nullglob
TEMPLATE_ZIPS=(.genreleases/spec-kit-template-*-${VERSION}.zip)
PYTHON_DIST=(dist/*.whl dist/*.tar.gz)
shopt -u nullglob

if [[ ${#TEMPLATE_ZIPS[@]} -eq 0 ]]; then
  echo "No template archives found for ${VERSION} under .genreleases/" >&2
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
