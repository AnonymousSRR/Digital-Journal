#!/usr/bin/env bash
set -euo pipefail

PLAN_DIR="stories and plans/implementation plans"
REVIEW_DIR="Plan Reviewer Results"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

log "Starting Coder → Plan-Reviewer pipeline"
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

# Ensure Copilot can access this repo directory
REPO_DIR="$(pwd)"

log "Latest plan detected: $LATEST_PLAN"
log "Step 1: Running Coder agent (full tool auto-approval)"

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

log "Step 2: Running Plan-Reviewer agent (compare UNCOMMITTED changes vs latest plan)"

mkdir -p "$REVIEW_DIR"

PLAN_BASENAME="$(basename "$LATEST_PLAN")"
PLAN_STEM="${PLAN_BASENAME%.md}"
PLAN_STEM="${PLAN_STEM#implementation_plan_}"

REVIEW_FILE="$REVIEW_DIR/plan_review_${PLAN_STEM}.md"

# Build a git snapshot that the reviewer can paste into the report
GIT_SNAPSHOT="$(git status --porcelain || true)"

copilot --agent="Plan-Reviewer" \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "You are the Plan-Reviewer agent.

TASK:
1) Use the latest implementation plan at: $LATEST_PLAN
2) Review ONLY the current UNCOMMITTED changes in this repo (working tree).
3) Produce a markdown review report with:
   - Overall Match: Yes/No
   - If Yes: only output Overall Match section and stop
   - If No: include concise phase-by-phase gaps and actionable fixes
4) You MUST create the report file at:
   $REVIEW_FILE

IMPORTANT:
- Treat the plan as the single source of truth.
- Use git to determine uncommitted changes (git status/diff).
- Put the git status snapshot below into the report under Inputs.

GIT STATUS SNAPSHOT (git status --porcelain):
$GIT_SNAPSHOT

Implementation Plan Content:
$(cat "$LATEST_PLAN")"

log "Plan-Reviewer finished"
log "Review report expected at: $REVIEW_FILE"
log "Coder → Plan-Reviewer pipeline complete"
