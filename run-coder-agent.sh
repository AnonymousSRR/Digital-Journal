#!/usr/bin/env bash
set -euo pipefail

PLAN_DIR="stories and plans/implementation plans"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

log "Starting Coder pipeline"
log "Looking for latest plan in: $PLAN_DIR"

if [[ ! -d "$PLAN_DIR" ]]; then
  echo "[ERROR] Plan directory not found: $PLAN_DIR"
  exit 1
fi

LATEST_PLAN="$(ls -t "$PLAN_DIR"/implementation_plan_*.md 2>/dev/null | head -n 1 || true)"

if [[ -z "${LATEST_PLAN:-}" ]]; then
  echo "[ERROR] No implementation plan found in: $PLAN_DIR"
  echo "Expected files like: $PLAN_DIR/implementation_plan_<feature>.md"
  exit 1
fi

log "Latest plan detected: $LATEST_PLAN"
log "Step 1: Running Coder agent (full tool auto-approval)"

# Ensure Copilot can access this repo directory (recommended)
REPO_DIR="$(pwd)"

copilot --agent=Coder \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "Using the implementation plan below, implement the solution fully.
Add code and tests as required.
Run the tests as specified in the plan (and/or repo test scripts).
If you need dependencies, install them using the project's standard approach (pip / requirements.txt).
Do not claim tests passed unless you executed them.

Implementation Plan (FILE: $LATEST_PLAN):
$(cat "$LATEST_PLAN")"

log "Coder finished"
log "Coder pipeline complete"
