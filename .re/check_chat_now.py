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
    if not r.get("ok"): raise RuntimeError(f"raw {a:#x} fail")
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
r2 = send("dumpfuncsraw")
print("total functions:", r2.get("count"))
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    if "chat" in nm.lower():
        print(f"  i={f['i']} addr={f['addr']} outer={f['outer']} name={nm!r}")
S.close()
