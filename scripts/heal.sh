#!/usr/bin/env bash
# Direct script runner for PatchPilot Agent Skill
set -e

CMD=${1:-"pytest"}
MODEL=${2:-""}

if [ -n "$MODEL" ]; then
    python3 -m patchpilot.cli heal --cmd "$CMD" --model "$MODEL"
else
    python3 -m patchpilot.cli heal --cmd "$CMD"
fi
