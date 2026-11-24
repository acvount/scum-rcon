#!/usr/bin/env python3
"""scumctl.py — 外部控制 SCUM 服务端 harness（不启动游戏）

用法:
  python scumctl.py stat
  python scumctl.py classes
  python scumctl.py funcs chat
  python scumctl.py desc Chat_Server_BroadcastChatMessage
  python scumctl.py chat "YG" "76561198000000000" "hello from outside"
  python scumctl.py announce "服务器将在 10 分钟后重启"
  python scumctl.py give "YG" "/Game/SCUM/Items/BP_Item_AK47.BP_Item_AK47_C" 1
"""
import argparse, json, socket, sys

HOST, PORT = "127.0.0.1", 17880

def send(cmd: str, timeout=180.0) -> dict:
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    text = buf.decode("utf-8", "replace").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"ok": False, "raw": text}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs=argparse.REMAINDER)
    ns = ap.parse_args()
    if not ns.command:
        ap.print_help(); return 1
    cmd = " ".join('"%s"' % c if " " in c else c for c in ns.command)
    res = send(cmd)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("ok") else 2

if __name__ == "__main__":
    sys.exit(main())
