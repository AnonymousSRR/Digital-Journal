#!/usr/bin/env bash
set -euo pipefail

PLAN_DIR="stories and plans/implementation plans"
REVIEW_DIR="Plan Reviewer Results"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

log "Starting Coder → Plan-Reviewer → Auto-Fix pipeline"
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

REPO_DIR="$(pwd)"
mkdir -p "$REVIEW_DIR"

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

PLAN_BASENAME="$(basename "$LATEST_PLAN")"
PLAN_STEM="${PLAN_BASENAME%.md}"
PLAN_STEM="${PLAN_STEM#implementation_plan_}"

REVIEW_FILE="$REVIEW_DIR/plan_review_${PLAN_STEM}.md"

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

if [[ ! -f "$REVIEW_FILE" ]]; then
  echo "[ERROR] Plan review report was not created: $REVIEW_FILE"
  exit 1
fi

# Step 3: Auto-fix loop (Coder reads latest plan + latest review report)
log "Step 3: Checking Overall Match and applying fixes if needed"

# Detect Overall Match (case-insensitive) from the review file
OVERALL_MATCH="$(grep -iE '^\*\*Overall Match\*\*:\s*(Yes|No)\s*$' "$REVIEW_FILE" \
  | head -n 1 \
  | sed -E 's/.*:\s*(Yes|No)\s*$/\1/I' || true)"

# Fallback if formatting differs slightly
if [[ -z "${OVERALL_MATCH:-}" ]]; then
  OVERALL_MATCH="$(grep -iE 'Overall Match' "$REVIEW_FILE" \
    | head -n 1 \
    | sed -E 's/.*(Yes|No).*/\1/I' || true)"
fi

if [[ -z "${OVERALL_MATCH:-}" ]]; then
  echo "[ERROR] Could not determine Overall Match (Yes/No) from: $REVIEW_FILE"
  echo "Make sure the review file contains a line like: **Overall Match**: Yes"
  exit 1
fi

log "Plan review Overall Match: $OVERALL_MATCH"

if [[ "${OVERALL_MATCH,,}" == "yes" ]]; then
  log "Overall Match is Yes — no auto-fix required."
  log "Pipeline complete."
  exit 0
fi

log "Overall Match is No — running Coder agent to apply fixes from review report"

copilot --agent=Coder \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "You are the Coder agent.

GOAL:
Bring the codebase into full alignment with the implementation plan by applying ONLY the fixes called out in the Plan Review Report.

RULES:
- Use the implementation plan as the single source of truth.
- Use the Plan Review Report to identify missing/mismatched items and fix them.
- Implement the missing parts, update code, update tests, and rerun relevant tests.
- Do not add scope beyond what the plan requires.
- Do not claim tests passed unless you executed them.
- After applying fixes, ensure the working tree reflects those updates.

LATEST IMPLEMENTATION PLAN (FILE: $LATEST_PLAN):
$(cat "$LATEST_PLAN")

LATEST PLAN REVIEW REPORT (FILE: $REVIEW_FILE):
$(cat "$REVIEW_FILE")"

log "Auto-fix Coder run finished"
log "Pipeline complete (Coder → Plan-Reviewer → Auto-Fix)"
