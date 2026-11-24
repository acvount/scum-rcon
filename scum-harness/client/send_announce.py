# -*- coding: utf-8 -*-
import json, socket, struct, sys
S = socket.create_connection(("127.0.0.1", 17880), timeout=240)
def send(cmd):
    S.sendall((cmd + "\n").encode("utf-8")); buf = b""
    while not buf.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def dn(pool, nid):
    if nid <= 0: return ""
    blk = rd64(pool + 0x10 + ((nid >> 16) * 8))
    if not blk: return ""
    off = (nid & 0xFFFF) * 2
    hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if ln == 0 or ln > 512: return "?%d" % nid
    d = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack("<%dH" % ln, d)) if wide else d.decode("latin1")

TEXT = "\u4f60\u597d"   # 你好

st = send("stat"); pool = int(st["names"], 16)
funcs = send("dumpfuncsraw").get("functions", [])
addr = {}
for f in funcs:
    nm = dn(pool, f["nameId"])
    if nm in ("BroadcastChatLine", "Multicast_DisplayNotification", "Multicast_ShowEventNotification", "SendChatLineToPlayer"):
        addr.setdefault(nm, int(f["addr"]))

# WorldContextObject: 取 outer 名为 PersistentLevel 的 GameMode 活实例
ctx = 0
r = send("findinst BP_ConZGameMode_C 10")
for it in r.get("items", []):
    a = int(it["addr"]); outer = struct.unpack("<Q", raw(a, 0x28)[0x20:0x28])[0]
    if not outer: continue
    if dn(pool, struct.unpack("<I", raw(outer + 0x18, 4))[0]) == "PersistentLevel":
        ctx = a; break
print("ctx = %#x" % ctx)
print("BroadcastChatLine = %#x" % addr.get("BroadcastChatLine", 0))
print("Multicast_DisplayNotification = %#x" % addr.get("Multicast_DisplayNotification", 0))

results = {}
# 1) 聊天行（全局频道 0）
if addr.get("BroadcastChatLine") and ctx:
    results["chatline"] = send("gtcallpe %#x %#x 0:o:%#x 0:s:%s 24:i:0" % (addr["BroadcastChatLine"], ctx, ctx, TEXT))
# 2) 屏幕通知条（SectorName@0 FString, FallDuration@16 float）
if addr.get("Multicast_DisplayNotification") and ctx:
    results["display"] = send("gtcallpe %#x %#x 0:s:%s 16:f:6.0" % (addr["Multicast_DisplayNotification"], ctx, TEXT))
# 3) 事件通知（Type byte@0, targetPrisoner obj@8）
if addr.get("Multicast_ShowEventNotification") and ctx:
    results["event"] = send("gtcallpe %#x %#x 0:b:0 8:o:0x%x" % (addr["Multicast_ShowEventNotification"], ctx, ctx))

print(json.dumps(results, ensure_ascii=True, indent=1))
S.close()
