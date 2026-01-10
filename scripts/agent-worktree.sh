#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <branch-name> <worktree-path>"
  exit 1
fi

branch="$1"
worktree_path="$2"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: run from inside a git repository."
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/$branch"; then
  git worktree add "$worktree_path" "$branch"
else
  git worktree add -b "$branch" "$worktree_path"
fi
