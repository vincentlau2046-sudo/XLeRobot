# XLeRobot 校准备份索引

| 日期 | 事件 | 目录 |
|------|------|------|
| 2026-07-21 | 左臂驱动板更换 + 14电机完整校准 | `20260721_left_arm_replacement/` |
| (历史) | 旧校准 | 见 Pi `~/robot_code/calibration_backup_*` |

## 脚本
- `v4_scripts/calibrate_v4.py`: 2026-07-21 使用的引导校准脚本
  - 交互式，每关节两步（中点定位→全程摇动）
  - 不写 EEPROM range，仅存 JSON
