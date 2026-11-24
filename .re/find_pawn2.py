import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=240)
def send(cmd):
    S.sendall((cmd + "\n").encode()); b = b""
    while not b.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        b += c
    return json.loads(b.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def dn(pool, nid):
    if nid <= 0: return ""
    blk = rd64(pool + 0x10 + ((nid >> 16) * 8)); off = (nid & 0xFFFF) * 2
    hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if not blk or ln == 0 or ln > 512: return f"?{nid}"
    d = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", d)) if wide else d.decode("latin1")

st = send("stat"); pool = int(st["names"], 16)
r = send("findinst BP_ConZGameMode_C 10")
for it in r.get("items", []):
    a = int(it["addr"])
    outer = struct.unpack("<Q", raw(a + 0x20, 8))[0]
    on = dn(pool, struct.unpack("<I", raw(outer + 0x18, 4))[0]) if outer else ""
    print("GameMode i=%s addr=%#x outer=%#x outerName=%r" % (it["i"], a, outer, on))
    if on == "PersistentLevel":
        r2 = send("findbyouter %x 80" % outer)
        print("  children:", r2.get("count"))
        for c in r2.get("items", [])[:40]:
            print("   ", c["i"], repr(dn(pool, c["nameId"])), c.get("class"))
S.close()
