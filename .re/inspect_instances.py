# 检查 GameMode 候选对象的标志/outer，找真正带世界的实例
import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=120)
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
for cls in ("BP_ConZGameMode_C", "BP_ConZGameState_C", "BP_ConZPlayerController_C"):
    r = send(f"findinst {cls} 10")
    print(f"=== {cls}: {r.get('count')} 个 ===")
    for it in r.get("items", []):
        addr = int(it["addr"])
        b = raw(addr, 0x28)
        flags = struct.unpack("<I", b[8:12])[0]
        idx = struct.unpack("<I", b[12:16])[0]
        name = struct.unpack("<II", b[0x18:0x20])
        outer = struct.unpack("<Q", b[0x20:0x28])[0]
        nm = decode_name(pool, name[0])
        on = decode_name(pool, struct.unpack("<I", raw(outer + 0x18, 4))[0]) if outer else ""
        print(f"  i={it['i']} addr={addr:#x} flags={flags:#x} idx={idx} name={nm!r} outer={outer:#x} outerName={on!r}")
S.close()
