#!/usr/bin/env bash
set -euo pipefail

REQ="We want to create implementation plan for user emotion analysis"

PLAN_DIR="stories and plans"
PLAN_FILE="$PLAN_DIR/implementation_plan.md"

log() {
  echo "[$(date '+%H:%M:%S')] $1"
}

mkdir -p "$PLAN_DIR"

log "Starting Planner pipeline"
log "Requirement: $REQ"
log "Step 1: Running Planner agent"

TMP_OUT="$(mktemp)"

# 1) Ask planner to wrap the plan with clear markers
# 2) Capture ALL output into a temp file (so terminal still stays clean-ish)
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

# Extract only what’s between the markers into the plan file
awk '
  $0=="===PLAN_START===" {inplan=1; next}
  $0=="===PLAN_END==="   {inplan=0}
  inplan {print}
' "$TMP_OUT" > "$PLAN_FILE"

rm -f "$TMP_OUT"

log "Planner finished"
log "Plan saved to $PLAN_FILE"
