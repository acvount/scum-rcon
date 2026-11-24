import json, socket, struct
def send(cmd, timeout=120):
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
r = send("findobj BP_ConZGameMode_C 10")
for it in r.get("items", []):
    if it["class"] == "":
        d = send(f"dumpidx {it['i']}")
        addr = int(d["addr"], 16)
        print(f"=== GameMode class obj idx={it['i']} addr={addr:#x} name={it['name']} ===")
        r2 = send(f"findbyouter {addr:x} 300")
        print("children:", r2.get("count"))
        for k in r2.get("items", [])[:60]:
            nm = decode_name(pool, k["nameId"])
            print(f"  i={k['i']} name={nm!r} class={k['class']}")
