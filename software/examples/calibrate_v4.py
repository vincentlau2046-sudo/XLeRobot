#!/usr/bin/env python3.10
import json, os, time, sys, select, serial

ADDR_TORQUE_ENABLE = 0x28
ADDR_PRESENT_POS = 0x38
ADDR_LOCK = 0x31
ADDR_OP_MODE = 0x2D
ADDR_HOMING_OFFSET = 0x1F
SCS_INST_READ = 0x02
SCS_INST_WRITE = 0x03
TQ_DISABLE = 0
TQ_ENABLE = 1

def crc(p):
    p[-1] = (~sum(p[2:-1])) & 0xFF; return p
def rpkt(m, a, n):
    return crc(bytearray([0xFF,0xFF,m,0x04,SCS_INST_READ,a&0xFF,n&0xFF,0x00]))
def wpkt(m, a, d):
    params=[a&0xFF]+d; pl=2+len(params)
    p=bytearray(5+len(params)); p[0]=0xFF;p[1]=0xFF;p[2]=m;p[3]=pl;p[4]=SCS_INST_WRITE
    for i,v in enumerate(params): p[5+i]=v
    p=bytearray(list(p)+[0x00]); return crc(p)

def rd(ser,m,a,n):
    ser.reset_input_buffer(); ser.write(rpkt(m,a,n)); time.sleep(0.06)
    r=ser.read(256)
    if len(r)>=7:
        for i in range(len(r)-5):
            if r[i]==0xFF and r[i+1]==0xFF and r[i+2]==m:
                d=list(r[i+5:i+5+r[i+3]-2])
                return sum(d[j]<<(8*j) for j in range(len(d)))
    return None

def wr(ser,m,a,v,n):
    d=[(v>>(8*i))&0xFF for i in range(n)]
    ser.reset_input_buffer(); ser.write(wpkt(m,a,d)); time.sleep(0.03)

def enc_sm(v):
    return (v&0x7FFF)|((1<<15) if v<0 else 0)

BUSES = [
    {"port":"/dev/ttyACM0","label":"左臂+头部","motors":[
        (1,"left_arm_shoulder_pan","左肩水平旋转"),
        (2,"left_arm_shoulder_lift","左肩垂直抬升"),
        (3,"left_arm_elbow_flex","左肘弯曲"),
        (4,"left_arm_wrist_flex","左腕俯仰"),
        (5,"left_arm_wrist_roll","左腕旋转"),
        (6,"left_arm_gripper","左夹爪开合"),
        (7,"head_motor_1","头部水平(pan)"),
        (8,"head_motor_2","头部俯仰(tilt)"),
    ]},
    {"port":"/dev/ttyACM1","label":"右臂","motors":[
        (1,"right_arm_shoulder_pan","右肩水平旋转"),
        (2,"right_arm_shoulder_lift","右肩垂直抬升"),
        (3,"right_arm_elbow_flex","右肘弯曲"),
        (4,"right_arm_wrist_flex","右腕俯仰"),
        (5,"right_arm_wrist_roll","右腕旋转"),
        (6,"right_arm_gripper","右夹爪开合"),
    ]}
]

CAL_PATH = "/root/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json"
with open(CAL_PATH) as f:
    cal = json.load(f)

print("="*70); print("  XLeRobot 校准 v4 (只写JSON，不写EEPROM)"); print("  "+time.strftime("%Y-%m-%d %H:%M:%S")); print("="*70)

for bc in BUSES:
    print("\n"+"="*70); print("  %s — %s" % (bc["label"], bc["port"])); print("="*70)
    try:
        ser = serial.Serial(bc["port"], 1000000, timeout=0.3)
    except Exception as e:
        print("  ❌ %s" % e); continue
    time.sleep(0.2); ser.reset_input_buffer()

    for mid, name, desc in bc["motors"]:
        print("\n"+"-"*70)
        print("  【%s】ID=%d — %s" % (name, mid, desc))
        print("-"*70)

        # 先解锁+禁用力矩
        wr(ser, mid, ADDR_LOCK, 0, 1); time.sleep(0.02)
        wr(ser, mid, ADDR_TORQUE_ENABLE, TQ_DISABLE, 1); time.sleep(0.03)
        wr(ser, mid, ADDR_OP_MODE, 0, 1); time.sleep(0.02)

        tq = rd(ser, mid, ADDR_TORQUE_ENABLE, 1)
        pos = rd(ser, mid, ADDR_PRESENT_POS, 2)
        print("  力矩=%s 位置=%s (应能自由活动)" % (str(tq), str(pos)))
        if tq != 0:
            print("  ⚠️ 力矩未释放，尝试再次...")
            wr(ser, mid, ADDR_LOCK, 0, 1); time.sleep(0.02)
            wr(ser, mid, ADDR_TORQUE_ENABLE, TQ_DISABLE, 1); time.sleep(0.03)
            tq = rd(ser, mid, ADDR_TORQUE_ENABLE, 1)
            print("  力矩=%s" % str(tq))

        # Step 1: 中点
        print("  ► 第1步: 把 %s 移到物理中间位置" % desc)
        input("    放好后按 Enter > ")

        pos_mid = rd(ser, mid, ADDR_PRESENT_POS, 2)
        if pos_mid is None:
            print("  ❌ 读取失败，跳过"); continue
        new_off = -(pos_mid - 2048)
        wr(ser, mid, ADDR_HOMING_OFFSET, enc_sm(new_off), 2)
        time.sleep(0.05)
        v = rd(ser, mid, ADDR_PRESENT_POS, 2)
        print("  pos=%d → offset=%d → 回读=%s ✅" % (pos_mid, new_off, str(v)))

        # Step 2: 摇动记录（不写EEPROM range，只存JSON）
        print("  ► 第2步: 缓慢全程摇动 %s" % desc)
        print("    按 Enter 开始，再按 Enter 结束")
        input("    > ")

        samples = []
        while True:
            if select.select([sys.stdin],[],[],0)[0]:
                sys.stdin.readline(); break
            p = rd(ser, mid, ADDR_PRESENT_POS, 2)
            if p is not None: samples.append(p)
            if len(samples)%15==0 and samples:
                print("\r    采样 %d  min=%d  max=%d  " % (len(samples),min(samples),max(samples)), end="", flush=True)
            time.sleep(0.03)

        print()
        if len(samples)>=5:
            rmin, rmax = min(samples), max(samples)
            print("  range=[%d, %d] 跨度=%d ✅" % (rmin, rmax, rmax-rmin))
        else:
            rmin, rmax = 0, 4095
            print("  采样不足(%d)，设全范围" % len(samples))

        # 只存JSON，不写EEPROM
        cal[name] = {"id": mid, "drive_mode": 0, "homing_offset": new_off, "range_min": rmin, "range_max": rmax}
        print("  ✅ %s 完成" % desc)

    ser.close()

with open(CAL_PATH, "w") as f:
    json.dump(cal, f, indent=2)
bkp_dir = os.path.expanduser("~/calib_v4_"+time.strftime("%Y%m%d_%H%M%S"))
os.makedirs(bkp_dir, exist_ok=True)
with open(os.path.join(bkp_dir,"calibration.json"),"w") as f:
    json.dump(cal,f,indent=2)

print("\n"+"="*70)
print("  校准完成!")
for k in sorted(cal.keys()):
    v=cal[k]; print("  %-30s: ID=%d offset=%5d range=[%d,%d]"%(k,v["id"],v["homing_offset"],v["range_min"],v["range_max"]))
print("="*70)
