"""ZMQ Client (Pi Robot Client) — Pi connects to PC Host.

Architecture: Pi is the robot client. It connects to PC's ZMQ ports.
PC binds as the compute host.

Data flow:
  Port 5555: PC PUSH bind → Pi PULL connect (commands: PC→Pi)
  Port 5556: PC PULL bind → Pi PUSH connect (observations: Pi→PC)

Usage (inside xlerobot container):
  python3.10 zmq_client.py --pc-host 192.168.2.227

Environment variables:
  PC_HOST  - PC IP address (default: 192.168.2.227)
  CMD_PORT - Command port (default: 5555)
  OBS_PORT - Observation port (default: 5556)
"""
import sys
import os
import time
import json
import base64
import argparse

sys.path.insert(0, "/home/XLeRobot-main/lerobot/src")

import zmq
import cv2
import numpy as np

from lerobot.robots.xlerobot.xlerobot import XLerobot
from lerobot.robots.xlerobot.config_xlerobot import XLerobotConfig


def main():
    parser = argparse.ArgumentParser(description="XLeRobot ZMQ Client (Pi Robot)")
    parser.add_argument("--pc-host", type=str, default=os.environ.get("PC_HOST", "192.168.2.227"),
                        help="PC host IP address")
    parser.add_argument("--cmd-port", type=int, default=int(os.environ.get("CMD_PORT", "5555")),
                        help="Command port on PC")
    parser.add_argument("--obs-port", type=int, default=int(os.environ.get("OBS_PORT", "5556")),
                        help="Observation port on PC")
    args = parser.parse_args()

    config = XLerobotConfig()
    robot = XLerobot(config)

    # 1. Connect robot (skip calibration)
    print("[CLIENT] Connecting robot...", flush=True)
    robot.connect(calibrate=False)
    print(f"[CLIENT] Connected: bus1={robot.bus1.is_connected} bus2={robot.bus2.is_connected}", flush=True)

    # 2. Warm up cameras (staggered, longer timeout)
    print("[CLIENT] Warming up cameras...", flush=True)
    for name, cam in robot.cameras.items():
        for attempt in range(3):
            try:
                cam.async_read(timeout_ms=3000)
                print(f"[CLIENT]   Camera {name}: OK", flush=True)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.3)
                else:
                    print(f"[CLIENT]   Camera {name}: warmup FAILED: {e}", flush=True)

    # 3. Connect to PC Host (Pi is the client, connects to PC's bound ports)
    ctx = zmq.Context()

    # Command channel: Pi PULL connects to PC's PUSH bind
    cmd_sock = ctx.socket(zmq.PULL)
    cmd_sock.connect(f"tcp://{args.pc_host}:{args.cmd_port}")
    cmd_sock.setsockopt(zmq.CONFLATE, 1)

    # Observation channel: Pi PUSH connects to PC's PULL bind
    obs_sock = ctx.socket(zmq.PUSH)
    obs_sock.connect(f"tcp://{args.pc_host}:{args.obs_port}")
    obs_sock.setsockopt(zmq.CONFLATE, 1)

    print(f"[CLIENT] Connected to PC {args.pc_host}: PULL cmd:{args.cmd_port} / PUSH obs:{args.obs_port}", flush=True)

    # 4. Main loop
    last_cmd_time = time.time()
    WATCHDOG_MS = 500
    loop_interval = 1.0 / 30  # 30 Hz

    try:
        while True:
            loop_start = time.time()

            # Receive commands (non-blocking)
            try:
                msg = cmd_sock.recv_string(zmq.NOBLOCK)
                data = json.loads(msg)
                robot.send_action(data)
                last_cmd_time = time.time()
            except zmq.Again:
                pass
            except Exception as e:
                print(f"[CLIENT] Cmd error: {e}", flush=True)

            # Watchdog: stop base if no command for too long
            if time.time() - last_cmd_time > WATCHDOG_MS / 1000:
                robot.stop_base()

            # Get observation & encode
            obs = robot.get_observation()
            for cam_key in robot.cameras:
                ret, buf = cv2.imencode(".jpg", obs[cam_key], [cv2.IMWRITE_JPEG_QUALITY, 90])
                obs[cam_key] = base64.b64encode(buf).decode("utf-8") if ret else ""

            # Push observation
            try:
                obs_sock.send_string(json.dumps(obs), zmq.NOBLOCK)
            except zmq.Again:
                pass  # PC not ready

            # Maintain loop rate
            elapsed = time.time() - loop_start
            if elapsed < loop_interval:
                time.sleep(loop_interval - elapsed)

    except KeyboardInterrupt:
        print("\n[CLIENT] Interrupted", flush=True)
    finally:
        robot.disconnect()
        cmd_sock.close()
        obs_sock.close()
        ctx.term()
        print("[CLIENT] Shutdown", flush=True)


if __name__ == "__main__":
    main()
