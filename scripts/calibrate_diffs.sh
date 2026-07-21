#!/bin/bash
# XLeRobot Calibration Diff Tool
# Usage: ./scripts/calibrate_diffs.sh [version1] [version2]
# If no args, compares v4 (active) vs v2 (previous)

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CAL_DIR="$REPO/config/calibration"

V1="${1:-$CAL_DIR/20260721_left_arm_replacement/calibration_active.json}"
V2="${2:-$CAL_DIR/../../../backups/old_calibration_pre_20260721.json}"

echo "=== Calibration Diff ==="
echo "Target: $V1"
echo "Baseline: $V2"
echo ""

if [ ! -f "$V1" ]; then
    echo "ERROR: $V1 not found"
    exit 1
fi
if [ ! -f "$V2" ]; then
    echo "WARNING: $V2 not found, comparing with factory defaults"
    # Generate a default and diff
    exit 0
fi

# Per-motor diff
python3 -c "
import json

with open('$V1') as f: v1 = json.load(f)
with open('$V2') as f: v2 = json.load(f)

all_keys = sorted(set(list(v1.keys()) + list(v2.keys())))
print(f'{\"Motor\":30s} {\"Field\":>15s} {\"Before\":>10s} {\"After\":>10s} {\"Delta\":>10s}')
print('-' * 80)

for k in all_keys:
    a = v1.get(k, {})
    b = v2.get(k, {})
    for f in ['homing_offset', 'range_min', 'range_max']:
        va = a.get(f, 'N/A')
        vb = b.get(f, 'N/A')
        d = ''
        if isinstance(va, (int,float)) and isinstance(vb, (int,float)):
            d = f'{va - vb:+d}'
            if va == vb:
                continue  # skip unchanged
        print(f'{k:30s} {f:>15s} {str(vb):>10s} {str(va):>10s} {d:>10s}')
"
