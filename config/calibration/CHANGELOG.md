# XLeRobot Calibration Changelog

## v4 — 2026-07-21 (ACTIVE)
### Change Summary
- **Hardware**: Left arm driver board replaced
- **Port swap**: Physical cables re-routed to match code defaults
  ```
  Before: ACM0=right+base(9), ACM1=left+head(8)
  After:  ACM0=left+head(8),  ACM1=right+base(9)
  ```
- **Calibrated motors**: 14 (left arm 6, head 2, right arm 6)
- **Skipped**: Base wheels (3, full rotation 0-4095)

### Calibration Script Changes (v4 vs v3)
| Change | v3 (Old) | v4 (Current) | Reason |
|--------|----------|--------------|--------|
| EEPROM unlock | Lock=0 + disable torque | Same + verify | New board had Lock=1 |
| Range save | Written to EEPROM | JSON only | EEPROM write locked motor |
| Python req | python3.10 + pyserial | Same | Container has 3.12 (no pip) |

### Diff from v2 (2026-07-14)
See generated diff in `v4_diffs/` or run:
```bash
scripts/calibrate_diffs.sh
```

## v2 — 2026-07-14 (History)
- First calibration via XLerobot.calibrate()
- 17 motors calibrated
- head_motor_2 range bug (range=1) fixed in 2nd pass

## v1 — 2026-07-14 (Factory Default)
- Factory defaults, no calibration applied
