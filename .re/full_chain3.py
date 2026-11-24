# 完整链条 v3：单持久连接 + 批量解码
import json, socket, struct, sys

S = socket.create_connection(("127.0.0.1", 17880), timeout=180)

def send(cmd, timeout=180):
    S.sendall((cmd + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): raise RuntimeError(f"raw {a:#x} fail")
    return bytes.fromhex(r["hex"])

def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]

def decode_name(pool, nid):
    if nid <= 0: return ""
    block = nid >> 16; off = (nid & 0xFFFF) * 2
    if block > 1024: return f"?{nid}"
    try:
        blk = rd64(pool + 0x10 + block * 8)
    except Exception:
        return f"?{nid}"
    if not blk: return ""
    try:
        hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    except Exception:
        return f"?{nid}"
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if ln == 0 or ln > 512: return f"?{nid}"
    try:
        data = raw(blk + off + 2, ln * (2 if wide else 1))
    except Exception:
        return f"?{nid}"
    try:
        if wide:
            return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", data))
        return data.decode("latin1")
    except Exception:
        return f"?{nid}"

st = send("stat"); pool = int(st["names"], 16)
pr = send("tickprobe 87 19 2500")
tid = pr["tids"][0] if pr.get("tids") else 0
print("tid:", tid)
r = send(f'gtload "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C" 86 14 {tid} GameEngine 1')
cp = int(r["classPtr"])
print("gtload fired:", r.get("fired"), "ex:", r.get("ex"), "classPtr:", hex(cp))
r2 = send("dumpfuncsraw")
print("total functions:", r2.get("count"))
hits = []
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    low = nm.lower()
    if "chat" in low or "teleport" in low or "admin" in low or "announce" in low or "notif" in low:
        hits.append((f, nm))
print(f"=== matched {len(hits)} functions ===")
for f, nm in hits:
    print(f"  i={f['i']} addr={f['addr']} outer={f['outer']} name={nm!r}")
S.close()
