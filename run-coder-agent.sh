#!/usr/bin/env bash
set -euo pipefail

PLAN_DIR="stories and plans/implementation plans"
REVIEW_DIR="Plan Reviewer Results"
CODE_REVIEW_DIR="Code Reviewer Results"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

log "Starting Coder → Plan-Reviewer → Auto-Fix → Code-Reviewer → Code-Fix → PR-Maker pipeline"
log "Looking for latest plan in: $PLAN_DIR"

# ----------------------------
# STEP 0: Sanity checks
# ----------------------------
if [[ ! -d "$PLAN_DIR" ]]; then
  echo "[ERROR] Plan directory not found: $PLAN_DIR"
  exit 1
fi

LATEST_PLAN="$(ls -t "$PLAN_DIR"/implementation_plan_*.md 2>/dev/null | head -n 1 || true)"
if [[ -z "${LATEST_PLAN:-}" ]]; then
  echo "[ERROR] No implementation plan found in: $PLAN_DIR"
  exit 1
fi

REPO_DIR="$(pwd)"
mkdir -p "$REVIEW_DIR" "$CODE_REVIEW_DIR"

log "Latest plan detected: $LATEST_PLAN"

# ----------------------------
# STEP 1: CODER (initial implementation)
# ----------------------------
log "Step 1: Running Coder agent (initial implementation)"

copilot --agent=Coder \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "Using the implementation plan below, implement the solution fully.
Add code and tests as required.
Run the tests as specified in the plan.
Do not claim tests passed unless you executed them.

Implementation Plan (FILE: $LATEST_PLAN):
$(cat "$LATEST_PLAN")"

log "Coder finished initial implementation"

# ----------------------------
# STEP 2: PLAN REVIEWER
# ----------------------------
log "Step 2: Running Plan-Reviewer agent"

PLAN_BASENAME="$(basename "$LATEST_PLAN")"
PLAN_STEM="${PLAN_BASENAME%.md}"
PLAN_STEM="${PLAN_STEM#implementation_plan_}"
PLAN_REVIEW_FILE="$REVIEW_DIR/plan_review_${PLAN_STEM}.md"

PLAN_GIT_SNAPSHOT="$(git status --porcelain || true)"

copilot --agent="Plan-Reviewer" \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "You are the Plan-Reviewer agent.

TASK:
1) Use the implementation plan at: $LATEST_PLAN
2) Review ONLY the current UNCOMMITTED changes.
3) Create a markdown report at:
   $PLAN_REVIEW_FILE
4) Output Overall Match: Yes/No

GIT STATUS SNAPSHOT:
$PLAN_GIT_SNAPSHOT

IMPLEMENTATION PLAN:
$(cat "$LATEST_PLAN")"

if [[ ! -f "$PLAN_REVIEW_FILE" ]]; then
  echo "[ERROR] Plan review report not created: $PLAN_REVIEW_FILE"
  exit 1
fi

log "Plan review completed"

# ----------------------------
# STEP 3: AUTO-FIX BASED ON PLAN REVIEW
# ----------------------------
PLAN_MATCH="$(awk '
  BEGIN { IGNORECASE=1 }
  /Overall Match/ {
    if ($0 ~ /Yes/) { print "yes"; exit }
    if ($0 ~ /No/)  { print "no";  exit }
  }
' "$PLAN_REVIEW_FILE" || true)"

if [[ "$PLAN_MATCH" = "no" ]]; then
  log "Plan review failed — applying fixes via Coder"

  copilot --agent=Coder \
    --allow-all-tools \
    --allow-all-paths \
    --add-dir "$REPO_DIR" \
    --prompt "You are the Coder agent.

GOAL:
Fix ONLY the gaps mentioned in the Plan Review Report.
Do not add scope beyond the implementation plan.

IMPLEMENTATION PLAN:
$(cat "$LATEST_PLAN")

PLAN REVIEW REPORT:
$(cat "$PLAN_REVIEW_FILE")"

  log "Auto-fix based on plan review finished"
else
  log "Plan review passed — no plan-level fixes required"
fi

# ----------------------------
# STEP 4: CODE REVIEWER
# ----------------------------
log "Step 4: Running Code-Reviewer agent"

TS="$(date '+%Y-%m-%d_%H%M%S')"
CODE_REVIEW_FILE="$CODE_REVIEW_DIR/code_review_${TS}.md"
CODE_GIT_SNAPSHOT="$(git status --porcelain || true)"

copilot --agent="Code-Reviewer" \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "You are the Code-Reviewer agent.

TASK:
1) Review ONLY current UNCOMMITTED changes.
2) Restrict analysis to changed files and lines.
3) Create a markdown report at:
   $CODE_REVIEW_FILE
4) Include Overall Match: Yes/No

GIT STATUS SNAPSHOT:
$CODE_GIT_SNAPSHOT"

if [[ ! -f "$CODE_REVIEW_FILE" ]]; then
  echo "[ERROR] Code review report not created: $CODE_REVIEW_FILE"
  exit 1
fi

log "Code review completed"

# ----------------------------
# STEP 5: AUTO-FIX BASED ON CODE REVIEW
# ----------------------------
log "Step 5: Evaluating Code Review result"

CODE_MATCH="$(awk '
  BEGIN { IGNORECASE=1 }
  /Overall Match/ {
    if ($0 ~ /Yes/) { print "yes"; exit }
    if ($0 ~ /No/)  { print "no";  exit }
  }
' "$CODE_REVIEW_FILE" || true)"

if [[ "$CODE_MATCH" = "no" ]]; then
  log "Code review failed — applying fixes via Coder"

  copilot --agent=Coder \
    --allow-all-tools \
    --allow-all-paths \
    --add-dir "$REPO_DIR" \
    --prompt "You are the Coder agent.

GOAL:
Fix ONLY the issues identified in the Code Review Report.
Do not refactor unrelated code.
Do not add new features.

CODE REVIEW REPORT:
$(cat "$CODE_REVIEW_FILE")"

  log "Auto-fix based on code review finished"
else
  log "Code review passed — no code-level fixes required"
fi

# ----------------------------
# STEP 6: PR-MAKER
# ----------------------------
log "Step 6: Running PR-Maker agent (stage + commit + push + PR on current branch)"

# Fresh snapshot so PR-Maker sees final state after all fixes
FINAL_GIT_SNAPSHOT="$(git status --porcelain || true)"

copilot --agent="PR-Maker" \
  --allow-all-tools \
  --allow-all-paths \
  --add-dir "$REPO_DIR" \
  --prompt "You are the PR-Maker agent.

TASK:
- Take ALL current uncommitted changes (tracked + untracked), stage safely, create ONE commit on the CURRENT branch (do not create a new branch), push, and create a GitHub Pull Request.
- If there are NO changes, do NOT create a PR.

CONTEXT:
- Latest implementation plan file: $LATEST_PLAN
- Latest plan review report: $PLAN_REVIEW_FILE
- Latest code review report: $CODE_REVIEW_FILE

GIT STATUS SNAPSHOT (git status --porcelain):
$FINAL_GIT_SNAPSHOT"

log "Pipeline complete: Coder → Plan-Reviewer → Auto-Fix → Code-Reviewer → Code-Fix → PR-Maker"
