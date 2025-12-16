#!/usr/bin/env bash
set -euo pipefail

REQ="We want to create implementation plan for user emotion analysis"

PLAN_DIR="stories and plans"
PLAN_FILE="$PLAN_DIR/implementation_plan.md"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

mkdir -p "$PLAN_DIR"

log "Starting Plan → Code pipeline"
log "Requirement: $REQ"

# ------------------------
# STEP 1: PLANNER
# ------------------------
log "Step 1: Running Planner agent"

TMP_OUT="$(mktemp)"

copilot --agent=Planner --allow-tool 'write' \
  --prompt "Create a detailed, phased implementation plan for the following requirement.

IMPORTANT OUTPUT FORMAT:
- Print the final plan ONLY between these two lines:
===PLAN_START===
...plan here...
===PLAN_END===

Requirement:
$REQ" \
  > "$TMP_OUT"

awk '
  $0=="===PLAN_START===" {inplan=1; next}
  $0=="===PLAN_END==="   {inplan=0}
  inplan {print}
' "$TMP_OUT" > "$PLAN_FILE"

rm -f "$TMP_OUT"

# Safety check: ensure plan file is not empty
if [[ ! -s "$PLAN_FILE" ]]; then
  echo "[ERROR] Plan extraction failed (no content between PLAN_START/PLAN_END). Not running coder."
  exit 1
fi

log "Planner finished"
log "Plan saved to $PLAN_FILE"

# ------------------------
# STEP 2: CODER
# ------------------------
log "Step 2: Running Coder agent (uses most recent plan)"

copilot --agent=Coder --allow-tool 'write' \
  --prompt "Using the implementation plan below, implement the solution fully.
Add code and tests as required.
Only make changes that are necessary to satisfy the plan.

Implementation Plan:
$(cat "$PLAN_FILE")"

log "Coder finished"
log "Pipeline complete"
