#!/bin/bash
# =========================================================
# publish-to-github.sh
# Initialises a local git repo and pushes to a new GitHub
# repository using the GitHub CLI (gh).
#
# Prerequisites:
#   brew install gh        (macOS)
#   sudo apt install gh    (Ubuntu)
#   gh auth login
# =========================================================

set -e

REPO_NAME="police-misconduct-db"
DESCRIPTION="Police Misconduct Database v2.0 — FastAPI + React + PostgreSQL"
VISIBILITY="public"   # change to "private" if preferred

cd "$(dirname "$0")"

echo "=== Initialising git repo ==="
git init
git add .
git commit -m "Initial commit — Police Misconduct Database v2.0"

echo ""
echo "=== Creating GitHub repository and pushing ==="
gh repo create "$REPO_NAME" \
  --description "$DESCRIPTION" \
  --"$VISIBILITY" \
  --source=. \
  --remote=origin \
  --push

echo ""
echo "=== Done! ==="
gh repo view --web
