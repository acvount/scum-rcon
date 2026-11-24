#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scum_chat.py — SCUM 服务器外部聊天广播工具
============================================
通过 scum-harness 控制端口(127.0.0.1:17880)驱动服务器:
  1. 探测游戏线程 tid（tickprobe 87）
  2. 游戏线程加载 BP_ConZPlayerController（gtload mode 1）
  3. 全函数扫描定位 BroadcastChatLine（主机侧 raw 解码 FName，绕过插件解码）
  4. 取 GameMode 实例作 WorldContextObject
  5. gtcall 在游戏线程调用 BroadcastChatLine 广播消息

用法:
  python scum_chat.py "你的消息"           # 广播到全局聊天
  python scum_chat.py "消息" --reload      # 强制重新加载类
  python scum_chat.py "消息" --port 17880  # 自定义控制端口
"""
import argparse
import json
import socket
import struct
import sys

DEFAULT_PORT = 17880
CLASS_PATH = "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C"


class Harness:
    def __init__(self, port):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=180)
        self.pool = None

    def send(self, cmd):
        self.s.sendall((cmd + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            c = self.s.recv(1 << 22)
            if not c:
                break
            buf += c
        return json.loads(buf.decode("utf-8", "replace").strip())

    def raw(self, addr, ln):
        r = self.send(f"raw {addr:x} {ln}")
        if not r.get("ok"):
            raise RuntimeError(f"raw {addr:#x} failed: {r}")
        return bytes.fromhex(r["hex"])

    def rd64(self, addr):
        return struct.unpack("<Q", self.raw(addr, 8))[0]

    def init_pool(self):
        st = self.send("stat")
        self.pool = int(st["names"], 16)

    def decode_name(self, nid):
        """主机侧解码 FName（block:off*2 布局，lenShift=6, header=2）"""
        if nid <= 0:
            return ""
        block = nid >> 16
        off = (nid & 0xFFFF) * 2
        if block > 1024:
            return f"?{nid}"
        try:
            blk = self.rd64(self.pool + 0x10 + block * 8)
            hdr = struct.unpack("<H", self.raw(blk + off, 2))[0]
        except Exception:
            return f"?{nid}"
        wide = hdr & 1
        ln = (hdr >> 6) & 0x3FF
        if not blk or ln == 0 or ln > 512:
            return f"?{nid}"
        data = self.raw(blk + off + 2, ln * (2 if wide else 1))
        if wide:
            return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", data))
        return data.decode("latin1")

    def probe_tid(self):
        r = self.send("tickprobe 87 19 2500")
        if not r.get("ok") or not r.get("tids"):
            raise RuntimeError(f"tickprobe failed: {r}")
        return r["tids"][0]

    def load_class(self):
        tid = self.probe_tid()
        r = self.send(f'gtload "{CLASS_PATH}" 86 14 {tid} GameEngine 1')
        if not r.get("fired"):
            raise RuntimeError(f"gtload did not fire: {r}")
        return r

    def find_function(self, name):
        r = self.send("dumpfuncsraw")
        for f in r.get("functions", []):
            if self.decode_name(f["nameId"]) == name:
                return int(f["addr"])
        return None

    def find_world_context(self):
        """取带真实世界的 GameMode 实例（outer=PersistentLevel 的那个；CDO 的 GetWorld() 为 null）"""
        r = self.send("findinst BP_ConZGameMode_C 10")
        cands = [int(it["addr"]) for it in r.get("items", [])]
        for addr in cands:
            try:
                b = self.raw(addr, 0x28)
                outer = struct.unpack("<Q", b[0x20:0x28])[0]
                if not outer:
                    continue
                nid = struct.unpack("<I", self.raw(outer + 0x18, 4))[0]
                oname = self.decode_name(nid)
                if oname == "PersistentLevel":
                    return addr
            except Exception:
                continue
        if cands:
            return cands[-1]
        r2 = self.send("findobj BP_ConZGameMode_C 10")
        for it in r2.get("items", []):
            if it.get("class") == "":
                d = self.send(f"dumpidx {it['i']}")
                return int(d["addr"], 16)
        raise RuntimeError("world context object not found")

    def call(self, fn_addr, args, use_pe=True):
        cmd = f"{'gtcallpe' if use_pe else 'gtcall'} 0x{fn_addr:x}"
        for a in args:
            cmd += " " + a
        return self.send(cmd)

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="SCUM 服务器外部聊天广播")
    ap.add_argument("message", help="要广播的消息文本")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--reload", action="store_true", help="强制重新加载类")
    ap.add_argument("--chattype", type=int, default=0, help="ChatType 枚举值，默认 0")
    ap.add_argument("--ctx", default="", help="WorldContextObject 说明符(0xADDR/@Class/对象名)，缺省自动找 GameMode 实例")
    args = ap.parse_args()

    h = Harness(args.port)
    try:
        h.init_pool()
        print(f"[1/4] 加载 BP_ConZPlayerController ...")
        try:
            r = h.load_class()
            print(f"      gtload: fired={r.get('fired')} ex={r.get('ex')} classPtr={r.get('classPtr')}")
        except RuntimeError as e:
            print(f"      gtload 未触发（{e}）；若类已由引擎加载则继续")

        print("[2/4] 定位 BroadcastChatLine ...")
        addr = h.find_function("BroadcastChatLine")
        if not addr:
            print("      ERROR: BroadcastChatLine 不在对象表（类可能未加载或被 GC）")
            sys.exit(1)
        print(f"      addr = {addr:#x}")

        print("[3/4] 定位 WorldContextObject ...")
        ctx = int(args.ctx, 0) if args.ctx.startswith("0x") else 0
        if not ctx:
            ctx = h.find_world_context()
        print(f"      ctx = {ctx:#x}")

        print("[4/4] 广播消息 ...")
        # 显式偏移（不依赖 desc 属性走查）：
        #   BroadcastChatLine(WorldContextObject@0, Text@8, ChatType@24)
        resp = h.call(addr, [f"0:o:0x{ctx:x}", f'8:s:"{args.message}"', f"24:i:{args.chattype}"])
        print(json.dumps(resp, ensure_ascii=False))
        ok = resp.get("fired") and resp.get("ex") == 0
        print("RESULT:", "SUCCESS" if ok else "FAILED")
        sys.exit(0 if ok else 1)
    finally:
        h.close()


if __name__ == "__main__":
    main()
