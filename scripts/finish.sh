#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

skip_tests=0
no_push=0
message=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-tests) skip_tests=1; shift ;;
    --no-push) no_push=1; shift ;;
    -m|--message) message="${2:-}"; shift 2 ;;
    *) message="$1"; shift ;;
  esac
done

changed_files="$( { git diff --name-only; git diff --cached --name-only; } | sort -u )"
if [[ -z "${changed_files}" ]]; then
  echo "No changes to commit."
  exit 0
fi

needs_tests=0
if [[ $skip_tests -eq 0 ]]; then
  if echo "${changed_files}" | rg -q '(\\.py$|^tests/|^src/|pyproject\\.toml$|uv\\.lock$)'; then
    needs_tests=1
  fi
fi

if [[ $needs_tests -eq 1 ]]; then
  echo "Running tests: uv run pytest"
  uv run pytest
else
  echo "Skipping tests (no Python-impacting changes detected or --skip-tests set)."
fi

git add -A

if git diff --cached --quiet; then
  echo "Nothing staged after git add -A (unexpected)."
  exit 1
fi

if [[ -z "${message}" ]]; then
  read -r -p "Commit message: " message
fi
if [[ -z "${message}" ]]; then
  echo "Commit message is required."
  exit 1
fi

git commit -m "${message}"

if [[ $no_push -eq 0 ]]; then
  git push
else
  echo "Committed locally (--no-push)."
fi
