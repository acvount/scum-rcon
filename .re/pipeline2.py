# 完整流水线 v2：probe → gtload → dumpfuncsraw 找函数地址 → gtcall 广播
import json, socket, struct
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
# 找 BroadcastChatLine 地址
r2 = send("dumpfuncsraw")
addr = None
for f in r2.get("functions", []):
    if decode_name(pool, f["nameId"]) == "BroadcastChatLine":
        addr = int(f["addr"]); break
if not addr:
    print("BroadcastChatLine NOT FOUND"); S.close(); raise SystemExit
print("BroadcastChatLine addr:", hex(addr))
d = send(f"descaddr {addr:x}")
print("desc:", json.dumps(d, ensure_ascii=False))
# 找 GameMode 实例（WorldContextObject）
w = send("findinst BP_ConZGameMode_C 10")
print("findinst GameMode:", json.dumps(w, ensure_ascii=False)[:400])
if not w.get("items"):
    # 退回：用类 CDO 地址（+0x118）
    r3 = send("findobj BP_ConZGameMode_C 10")
    for it in r3.get("items", []):
        if it["class"] == "":
            di = send(f"dumpidx {it['i']}")
            wc = int(di["addr"], 16)
            break
else:
    wc = int(w["items"][0]["addr"], 16)
print("worldctx:", hex(wc))
msg = "[YG] external harness broadcast test"
c = send(f'gtcall 0x{addr:x} o:0x{wc:x} s:{msg} i:0')
print("gtcall:", json.dumps(c, ensure_ascii=False))
S.close()
