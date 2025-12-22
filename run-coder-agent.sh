#!/usr/bin/env bash
set -euo pipefail

PLAN_DIR="stories and plans/implementation plans"
REVIEW_DIR="Plan Reviewer Results"
CODE_REVIEW_DIR="Code Reviewer Results"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

log "Starting Coder → Plan-Reviewer(loop) → Code-Reviewer(loop) → PR-Maker pipeline"
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
# STEP 2 + 3: PLAN-REVIEWER <=> CODER LOOP (max 3)
# ----------------------------
log "Step 2: Running Plan-Reviewer <=> Coder loop (max 3 iterations)"

PLAN_BASENAME="$(basename "$LATEST_PLAN")"
PLAN_STEM="${PLAN_BASENAME%.md}"
PLAN_STEM="${PLAN_STEM#implementation_plan_}"

PLAN_MATCH="no"
PLAN_REVIEW_FILE=""

for i in 1 2 3; do
  log "Plan review iteration: $i/3"

  PLAN_REVIEW_FILE="$REVIEW_DIR/plan_review_${PLAN_STEM}_iter${i}.md"
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

  PLAN_MATCH="$(awk '
    BEGIN { IGNORECASE=1 }
    /Overall Match/ {
      if ($0 ~ /: *Yes|Yes *$/) { print "yes"; exit }
      if ($0 ~ /: *No|No *$/)  { print "no";  exit }
    }
  ' "$PLAN_REVIEW_FILE" | head -n 1 || true)"

  if [[ -z "${PLAN_MATCH:-}" ]]; then
    echo "[ERROR] Could not parse Overall Match from: $PLAN_REVIEW_FILE"
    exit 1
  fi

  log "Plan review result (iter $i): $PLAN_MATCH"

  if [[ "$PLAN_MATCH" = "yes" ]]; then
    log "Plan review passed on iteration $i — exiting plan loop."
    break
  fi

  if [[ "$i" -lt 3 ]]; then
    log "Plan review is No — running Coder to apply fixes (iter $i)"
    copilot --agent=Coder \
      --allow-all-tools \
      --allow-all-paths \
      --add-dir "$REPO_DIR" \
      --prompt "You are the Coder agent.

GOAL:
Fix ONLY the gaps mentioned in the latest Plan Review Report.
Do not add scope beyond the implementation plan.

IMPLEMENTATION PLAN:
$(cat "$LATEST_PLAN")

LATEST PLAN REVIEW REPORT:
$(cat "$PLAN_REVIEW_FILE")"
    log "Coder fixes applied for iteration $i"
  else
    log "Reached max plan iterations (3). Proceeding to Code-Reviewer loop."
  fi
done

log "Plan loop complete. Latest plan review report: $PLAN_REVIEW_FILE"

# ----------------------------
# STEP 4 + 5: CODE-REVIEWER <=> CODER LOOP (max 3)
# ----------------------------
log "Step 4: Running Code-Reviewer <=> Coder loop (max 3 iterations)"

CODE_MATCH="no"
CODE_REVIEW_FILE=""

for j in 1 2 3; do
  log "Code review iteration: $j/3"

  TS="$(date '+%Y-%m-%d_%H%M%S')"
  CODE_REVIEW_FILE="$CODE_REVIEW_DIR/code_review_${TS}_iter${j}.md"
  CODE_GIT_SNAPSHOT="$(git status --porcelain || true)"

  copilot --agent="Code-Reviewer" \
    --allow-all-tools \
    --allow-all-paths \
    --add-dir "$REPO_DIR" \
    --prompt "You are the Code-Reviewer agent.

TASK:
1) Review ONLY current UNCOMMITTED changes (modified + untracked).
2) Restrict analysis to changed files and changed lines (use git diff / git status).
3) Create a SINGLE markdown report file at:
   $CODE_REVIEW_FILE
4) The report MUST include: **Overall Match**: Yes/No
   - If any Critical or High issue exists → Overall Match: No
   - Else → Overall Match: Yes

INPUTS:
- Git Status Snapshot (git status --porcelain):
$CODE_GIT_SNAPSHOT

NOTES:
- Do NOT ask questions.
- Do NOT refactor code in this run.
- You MUST create the file at the exact path above."

  if [[ ! -f "$CODE_REVIEW_FILE" ]]; then
    echo "[ERROR] Code review report not created: $CODE_REVIEW_FILE"
    exit 1
  fi

  CODE_MATCH="$(awk '
    BEGIN { IGNORECASE=1 }
    /Overall Match/ {
      if ($0 ~ /: *Yes|Yes *$/) { print "yes"; exit }
      if ($0 ~ /: *No|No *$/)  { print "no";  exit }
    }
  ' "$CODE_REVIEW_FILE" | head -n 1 || true)"

  if [[ -z "${CODE_MATCH:-}" ]]; then
    echo "[ERROR] Could not parse Overall Match from: $CODE_REVIEW_FILE"
    exit 1
  fi

  log "Code review result (iter $j): $CODE_MATCH"

  if [[ "$CODE_MATCH" = "yes" ]]; then
    log "Code review passed on iteration $j — exiting code loop."
    break
  fi

  if [[ "$j" -lt 3 ]]; then
    log "Code review is No — running Coder to apply fixes (iter $j)"
    copilot --agent=Coder \
      --allow-all-tools \
      --allow-all-paths \
      --add-dir "$REPO_DIR" \
      --prompt "You are the Coder agent.

GOAL:
Fix ONLY the issues identified in the latest Code Review Report.
Do not refactor unrelated code.
Do not add new features.

LATEST CODE REVIEW REPORT:
$(cat "$CODE_REVIEW_FILE")"
    log "Coder fixes applied for iteration $j"
  else
    log "Reached max code review iterations (3). Proceeding to PR-Maker."
  fi
done

log "Code loop complete. Latest code review report: $CODE_REVIEW_FILE"

# ----------------------------
# STEP 6: PR-MAKER
# ----------------------------
log "Step 6: Running PR-Maker agent (stage + commit + push + PR on current branch)"

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

log "Pipeline complete: Coder → Plan-Reviewer(loop) → Code-Reviewer(loop) → PR-Maker"
