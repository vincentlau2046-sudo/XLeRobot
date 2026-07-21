# 2026-07-21 左臂驱动板更换 + 完整校准

## 变更
- 左臂驱动板更换为新板
- 物理线序从错乱调回代码默认（ACM0=左臂+头, ACM1=右臂+底盘）
- 14 电机引导校准（左臂6+头部2+右臂6）

## 校准数据
- `calibration_active.json`: 当前容器内生效的校准数据
- 路径: 容器 `/root/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json`

## 校准脚本
- `backups/calibration/v4_scripts/calibrate_v4.py`: 校准执行脚本
- 容器路径: `/root/calibrate_v4.py`

## 校准结果摘要
```
左臂: shoulder_pan(-67 [135,4031]) shoulder_lift(1119 [33,4003])
      elbow_flex(208 [194,4046])   wrist_flex(-75 [1056,3346])
      wrist_roll(-34 [173,3970])   gripper(-207 [622,1492])
头部: head_1(1825 [1307,3447])     head_2(1639 [2173,3396])
右臂: shoulder_pan(1008 [1127,3044]) ...
底盘: 3轮全转 0-4095
```

## 关键修复
1. EEPROM Lock 解锁后禁用力矩（否则左臂新板锁死）
2. range 不写 EEPROM（仅存 JSON），避免舵机异常锁定
3. 容器内用 python3.10（pyserial），不用默认 python3.12（无 pip）
