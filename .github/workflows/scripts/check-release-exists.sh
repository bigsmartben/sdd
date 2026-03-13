#!/usr/bin/env bash
set -euo pipefail

# check-release-exists.sh
# Check if a GitHub release already exists for the given version
# Usage: check-release-exists.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
REPO="${GITHUB_REPOSITORY:-}"

if [[ -z "$REPO" ]]; then
  echo "Error: GITHUB_REPOSITORY is not set" >&2
  exit 1
fi

if gh release view "$VERSION" --repo "$REPO" >/dev/null 2>&1; then
  echo "exists=true" >> $GITHUB_OUTPUT
  echo "Release $VERSION already exists in $REPO, skipping..."
else
  echo "exists=false" >> $GITHUB_OUTPUT
  echo "Release $VERSION does not exist in $REPO, proceeding..."
fi
