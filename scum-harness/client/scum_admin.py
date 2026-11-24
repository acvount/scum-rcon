#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scum_admin.py — 通过注入插件在游戏线程执行 SCUM 管理员命令（#开头）
=====================================================================
原理：调用 BP_ConZPlayerController 的 PlayerRpcChannel 上的
      Chat_Server_ProcessAdminCommand(commandText) 原生 RPC，
      引擎会按“玩家在聊天框输入 #命令”的完整流程执行。

用法:
  python scum_admin.py "#SetGodMode 1"
  python scum_admin.py "#Announce 服务器公告"
  python scum_admin.py "#Teleport 玩家名 x y z"
  python scum_admin.py --list          # 列出全部可用命令类型
"""
import json
import socket
import struct
import sys

PORT = 17880


class H:
    def __init__(self, port=PORT):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=180)
        self.pool = None
        self.mod = None

    def send(self, cmd):
        self.s.sendall((cmd + "\n").encode())
        b = b""
        while not b.endswith(b"\n"):
            c = self.s.recv(1 << 22)
            if not c:
                break
            b += c
        return json.loads(b.decode("utf-8", "replace").strip())

    def raw(self, a, ln):
        r = self.send(f"raw {a:x} {ln}")
        if not r.get("ok"):
            raise RuntimeError(f"raw {a:#x} fail: {r}")
        return bytes.fromhex(r["hex"])

    def rd64(self, a):
        return struct.unpack("<Q", self.raw(a, 8))[0]

    def rdu32(self, a):
        return struct.unpack("<I", self.raw(a, 4))[0]

    def dn(self, nid):
        if nid <= 0:
            return ""
        try:
            blk = self.rd64(self.pool + 0x10 + ((nid >> 16) * 8))
            if not blk:
                return ""
            off = (nid & 0xFFFF) * 2
            hdr = struct.unpack("<H", self.raw(blk + off, 2))[0]
            wide = hdr & 1
            ln = (hdr >> 6) & 0x3FF
            if ln == 0 or ln > 512:
                return f"?{nid}"
            d = self.raw(blk + off + 2, ln * (2 if wide else 1))
            return ("".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", d))
                    if wide else d.decode("latin1"))
        except Exception:
            return f"?{nid}"

    def init(self):
        st = self.send("stat")
        self.pool = int(st["names"], 16)
        self.mod = int(st["module"], 16)
        return st

    def find_function(self, name):
        for f in self.send("dumpfuncsraw").get("functions", []):
            if self.dn(f["nameId"]) == name:
                return int(f["addr"]), int(f["outer"])
        return None, None

    def channels(self):
        """返回候选 (index, channel, owner) 列表（排除 /Script/SCUM 模板与 Default__ CDO）"""
        fn, cls = self.find_function("Chat_Server_ProcessAdminCommand")
        if not fn:
            return [], None
        cid = self.rdu32(cls + 0x18)
        out = []
        for it in self.send(f"findbyclassnameid {cid} 50").get("items", []):
            a = int(it["addr"])
            try:
                owner = struct.unpack("<Q", self.raw(a + 0x20, 8))[0]
                if not owner:
                    continue
                oname = self.dn(self.rdu32(owner + 0x18))
                if oname.startswith("Default__") or oname.startswith("/Script/"):
                    continue
                out.append((int(it["i"]), a, owner))
            except Exception:
                continue
        return out, fn

    def live_channel(self):
        """当前玩家的通道 = 对象索引最大的非 CDO 通道（最新创建）"""
        chs, fn = self.channels()
        if not chs:
            return fn, None, None
        chs.sort(key=lambda t: t[0])
        newest = chs[-1]
        return fn, newest[1], newest[2]

    def find_pawn_in(self, chan):
        try:
            ctrl = struct.unpack("<Q", self.raw(chan + 0x20, 8))[0]
        except Exception:
            return None, None
        cands = []
        for off in (0x250, 0x260, 0x2a0, 0x760, 0x790):
            try:
                v = struct.unpack("<Q", self.raw(ctrl + off, 8))[0]
                if 0x10000 < v < 0x7FFFFFFFFFFF:
                    cands.append(v)
            except Exception:
                pass
        buf = b""
        for start in range(0, 0x800, 0x200):
            try:
                buf += self.raw(ctrl + start, 0x200)
            except Exception:
                break
        for off in range(0, len(buf) - 8, 8):
            v = struct.unpack("<Q", buf[off:off + 8])[0]
            if 0x10000 < v < 0x7FFFFFFFFFFF:
                cands.append(v)
        for v in cands:
            if v in (ctrl, chan):
                continue
            try:
                vt = self.rd64(v)
                if not (self.mod <= vt < self.mod + 0x7F000000):
                    continue
                root = self.rd64(v + 0x130)
                if not (0x10000 < root < 0x7FFFFFFFFFFF):
                    continue
                loc = struct.unpack("<3f", self.raw(root + 0x1D0, 12))
                if abs(loc[0]) < 2e6 and abs(loc[1]) < 2e6 and abs(loc[2]) < 2e5 and abs(loc[0]) > 1000:
                    return v, ctrl
            except Exception:
                continue
        return None, ctrl

    def find_pawn(self, chan=None):
        if chan:
            return self.find_pawn_in(chan)
        _, chan, ctrl = self.live_channel()
        if not chan:
            return None, None
        return self.find_pawn_in(chan)

    def pawn_loc(self, pawn):
        root = self.rd64(pawn + 0x130)
        return struct.unpack("<3f", self.raw(root + 0x1D0, 12))

    def exec_admin(self, text):
        """text 可带或不带 '#'；服务端期望不带 #（客户端会先剥掉）"""
        text = text.strip()
        if text.startswith("#"):
            text = text[1:].strip()
        fn, chan, ctrl = self.live_channel()
        if not fn:
            return {"ok": False, "error": "Chat_Server_ProcessAdminCommand not found (class not loaded?)"}
        if not chan:
            return {"ok": False, "error": "no live PlayerRpcChannel - player offline?"}
        # ctx = 活的 RPC 通道（等价于该玩家的控制器发起）
        r = self.send(f'gtcallpe 0x{fn:x} 0x{chan:x} 0:s:"{text}"')
        r["channel"] = f"0x{chan:x}"
        r["controller"] = f"0x{ctrl:x}" if ctrl else None
        return r


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        sys.exit(0)
    h = H()
    st = h.init()
    if "--list" in args:
        r = h.send("findclass AdminCommand 5000")
        names = sorted({it["class"] for it in r.get("items", []) if it.get("class")})
        print(f"共 {len(names)} 种 AdminCommand 类：")
        for n in names:
            print("  #" + n.replace("AdminCommand_", ""))
        return
    if "--tp" in args:
        # --tp <dx> <dy> [playerName]：把玩家传送到当前坐标 + 偏移
        i = args.index("--tp")
        rest = args[i + 1:]
        dx = float(rest[0]) if len(rest) > 0 else 5000.0
        dy = float(rest[1]) if len(rest) > 1 else 5000.0
        pname = rest[2] if len(rest) > 2 else None
        fn, chan, ctrl = h.live_channel()
        pawn, _ = h.find_pawn(chan)
        if not pawn:
            print("[-] 找不到玩家角色（玩家离线？）")
            return
        before = h.pawn_loc(pawn)
        print(f"[*] pawn=0x{pawn:x} 当前坐标: {before}")
        tx, ty, tz = before[0] + dx, before[1] + dy, before[2] + 120.0
        # 正确语法: #Teleport <X> <Y> <Z> [Player]
        cmd = f"#Teleport {tx:.0f} {ty:.0f} {tz:.0f}" + (f" {pname}" if pname else "")
        print(f"[*] 执行: {cmd}")
        r = h.exec_admin(cmd)
        print("[*] 结果:", json.dumps(r, ensure_ascii=False))
        import time
        time.sleep(2)
        try:
            print(f"[*] 传送后坐标: {h.pawn_loc(pawn)}")
        except Exception as e:
            print("[-] 复查失败:", e)
        return
    text = " ".join(args)
    if text.startswith("#"):
        text = text[1:].strip()
    print(f"[*] objects={st['objects']}  发送命令: {text}")
    r = h.exec_admin(text)
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
