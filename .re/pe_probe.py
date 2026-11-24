# gtcallpe 测试：ProcessEvent 路径广播 + 对比直调
import json, socket, struct, sys
S = socket.create_connection(("127.0.0.1", 17880), timeout=180)
def send(cmd):
    S.sendall((cmd + "\n").encode()); buf = b""
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
def decode_name(pool, nid):
    if nid <= 0: return ""
    block = nid >> 16; off = (nid & 0xFFFF) * 2
    if block > 1024: return f"?{nid}"
    try:
        blk = rd64(pool + 0x10 + block * 8)
        hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    except Exception:
        return f"?{nid}"
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if not blk or ln == 0 or ln > 512: return f"?{nid}"
    data = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", data)) if wide else data.decode("latin1")

st = send("stat"); pool = int(st["names"], 16)
pr = send("tickprobe 87 19 2500")
tid = pr["tids"][0] if pr.get("tids") else 0
print("tid:", tid)
r = send(f'gtload "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C" 86 14 {tid} GameEngine 1')
print("gtload:", json.dumps(r, ensure_ascii=False))
r2 = send("dumpfuncsraw")
addr = None
for f in r2.get("functions", []):
    if decode_name(pool, f["nameId"]) == "BroadcastChatLine":
        addr = int(f["addr"]); break
print("BroadcastChatLine:", hex(addr) if addr else None)
# 活 GameMode 实例（outer=PersistentLevel）
w = send("findinst BP_ConZGameMode_C 10")
ctx = 0
for it in w.get("items", []):
    a = int(it["addr"])
    try:
        outer = struct.unpack("<Q", raw(a + 0x20, 8))[0]
        if outer:
            on = decode_name(pool, struct.unpack("<I", raw(outer + 0x18, 4))[0])
            if on == "PersistentLevel":
                ctx = a; break
    except Exception:
        pass
print("ctx:", hex(ctx))
# 1) 直调
c1 = send(f'gtcall 0x{addr:x} 0:o:0x{ctx:x} 8:s:"direct" 24:i:0')
print("gtcall   :", json.dumps(c1, ensure_ascii=False))
# 2) ProcessEvent
c2 = send(f'gtcallpe 0x{addr:x} 0:o:0x{ctx:x} 8:s:"via-processevent" 24:i:0')
print("gtcallpe :", json.dumps(c2, ensure_ascii=False))
S.close()
