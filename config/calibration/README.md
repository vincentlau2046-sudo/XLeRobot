# XLeRobot Calibration Backup System

## Version Index

| Date | Version | Event | Calibrated | Git |
|------|---------|-------|------------|-----|
| 2026-07-21 | **v4** (ACTIVE) | Left arm driver board replacement | 14 motors (L6+H2+R6) | `af0e413` |
| 2026-07-14 | v2 | First full calibration | 17 motors (L6+H2+R6+B3) | - |
| 2026-07-14 | v1 | Factory defaults | None | - |

## Directory Structure
```
config/calibration/
├── README.md                         ← This file (version index)
├── CHANGELOG.md                      ← Full changelog with diffs
├── 20260721_left_arm_replacement/    ← v4 calibration
│   ├── README.md                     ← Session-specific notes
│   └── calibration_active.json       ← Current active calibration
├── v4_scripts/
│   └── calibrate_v4.py               ← Calibration script used
└── v4_diffs/
    └── (auto-generated via diff_helper.sh)
```

## Scripts in this repo
| Path | Description |
|------|-------------|
| `software/examples/calibrate_v4.py` | Interactive calibration script (14 motors) |
| `scripts/calibrate_diffs.sh` | Diff helper - compare calibration versions |

## Pi Container Sync
| Item | Container Path |
|------|---------------|
| Active calibration | `/root/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json` |
| Calibration script | `/root/calibrate_v4.py` |
| README | `/root/calibration_README.md` |
| Changelog | `/root/calibration_CHANGELOG.md` |
