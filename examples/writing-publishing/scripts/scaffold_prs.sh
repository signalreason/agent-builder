#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required to scaffold draft PRs."
  exit 1
fi

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <branch-name> <title>"
  exit 1
fi

branch="$1"
title="$2"

gh pr create --draft --title "$title" --body-file templates/pr-body.md --head "$branch"
