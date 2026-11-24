# 完整链条 v2：probe tid → gtload → dumpfuncsraw → 主机解码找 Chat_Server_*
import json, socket, struct, sys
def send(cmd, timeout=180):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(1 << 20)
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
    blk = rd64(pool + 0x10 + block * 8)
    if not blk: return ""
    hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if ln == 0 or ln > 512: return ""
    data = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", data)) if wide else data.decode("latin1")

st = send("stat"); pool = int(st["names"], 16)
# 1) 探测 tid
pr = send("tickprobe 87 19 2500")
tid = pr["tids"][0] if pr.get("tids") else 0
print("tid:", tid)
# 2) 加载类
r = send(f'gtload "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C" 86 14 {tid} GameEngine 1')
cp = int(r["classPtr"])
print("gtload fired:", r.get("fired"), "ex:", r.get("ex"), "classPtr:", hex(cp))
# 3) 全函数扫描
r2 = send("dumpfuncsraw")
print("total functions:", r2.get("count"))
hits = []
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    if "Chat" in nm or "chat" in nm or "Admin" in nm or "Teleport" in nm:
        hits.append((f, nm))
print("=== chat/admin/teleport functions ===")
for f, nm in hits:
    print(f"  i={f['i']} addr={f['addr']} outer={f['outer']} name={nm!r}")
if not hits:
    # 找 outer == classPtr 的函数
    for f in r2.get("functions", []):
        if int(f["outer"], 16) == cp:
            nm = decode_name(pool, f["nameId"])
            print(f"  (outer==class) i={f['i']} name={nm!r}")
