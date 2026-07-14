"""ZMQ Server (PC Host) — PC binds, Pi connects.

Architecture: PC is the compute host. It binds ZMQ ports.
Pi connects as the robot client.

Data flow:
  Port 5555: PC PUSH bind → Pi PULL connect (commands: PC→Pi)
  Port 5556: PC PULL bind → Pi PUSH connect (observations: Pi→PC)

Usage:
  python zmq_server.py [--cmd-port 5555] [--obs-port 5556]
"""
import argparse
import json
import time
import zmq


def main():
    parser = argparse.ArgumentParser(description="XLeRobot ZMQ Server (PC Host)")
    parser.add_argument("--cmd-port", type=int, default=5555, help="Port for sending commands (PUSH bind)")
    parser.add_argument("--obs-port", type=int, default=5556, help="Port for receiving observations (PULL bind)")
    parser.add_argument("--test-duration", type=float, default=0, help="Run test for N seconds (0=infinite)")
    args = parser.parse_args()

    ctx = zmq.Context()

    # Bind command channel: PC sends, Pi receives
    cmd_sock = ctx.socket(zmq.PUSH)
    cmd_sock.bind(f"tcp://*:{args.cmd_port}")
    cmd_sock.setsockopt(zmq.CONFLATE, 1)

    # Bind observation channel: Pi sends, PC receives
    obs_sock = ctx.socket(zmq.PULL)
    obs_sock.bind(f"tcp://*:{args.obs_port}")
    obs_sock.setsockopt(zmq.CONFLATE, 1)

    print(f"[SERVER] PC Host ready: PUSH cmd:{args.cmd_port} / PULL obs:{args.obs_port}", flush=True)
    print(f"[SERVER] Waiting for Pi client to connect...", flush=True)

    poller = zmq.Poller()
    poller.register(obs_sock, zmq.POLLIN)

    obs_count = 0
    t0 = time.time()
    last_print = 0
    first_obs = None

    try:
        while True:
            # Receive observations
            socks = dict(poller.poll(1000))
            if obs_sock in socks:
                try:
                    msg = obs_sock.recv_string(zmq.NOBLOCK)
                    obs = json.loads(msg)
                    obs_count += 1

                    if first_obs is None:
                        first_obs = obs
                        keys = sorted(obs.keys())
                        cam_keys = [k for k in keys if isinstance(obs[k], str) and len(obs[k]) > 100]
                        motor_keys = [k for k in keys if k not in cam_keys]
                        print(f"[SERVER] ✅ Pi connected! First obs received")
                        print(f"  Motor keys ({len(motor_keys)}): {motor_keys}")
                        print(f"  Camera keys ({len(cam_keys)}): {cam_keys}")

                    now = time.time()
                    if now - last_print >= 5:
                        elapsed = now - t0
                        hz = obs_count / elapsed if elapsed > 0 else 0
                        print(f"  [{elapsed:.0f}s] obs_count={obs_count}, rate={hz:.1f} Hz", flush=True)
                        last_print = now

                except zmq.Again:
                    pass

            # Test mode: stop after duration
            if args.test_duration > 0 and time.time() - t0 >= args.test_duration:
                break

    except KeyboardInterrupt:
        print("\n[SERVER] Interrupted")

    elapsed = time.time() - t0
    hz = obs_count / elapsed if elapsed > 0 else 0
    print(f"\n[SERVER] Summary: {obs_count} obs in {elapsed:.1f}s = {hz:.1f} Hz")

    cmd_sock.close()
    obs_sock.close()
    ctx.term()


if __name__ == "__main__":
    main()
