import json, socket, struct
def send(cmd, timeout=60):
    with socket.create_connection(("127.0.0.1", 17880), timeout=60) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"):
        raise RuntimeError(f"raw {a:#x} fail: {r}")
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]

st = send("stat")
pool = int(st["names"], 16)
print("pool:", hex(pool))
for label, nid in [("new-class-name", 9406730), ("class-obj-name", 709885), ("known-GameMode-C", 0)]:
    if label == "known-GameMode-C":
        nid = None
        r = send("nameidx BP_ConZGameMode_C 5")
        for h in r.get("hits", []):
            if h["name"] == "BP_ConZGameMode_C":
                nid = h["id"]; break
        if nid is None:
            print("GameMode_C name not found"); continue
    block = nid >> 16
    off = (nid & 0xFFFF) * 2
    blk = rd64(pool + 0x10 + block * 8)
    print(f"{label}: id={nid} block={block} off={off} blockPtr={blk:#x}")
    b = raw(blk + off, 64)
    print("  bytes:", b.hex(" "))
    # 尝试 header=2 lenShift=6
    hdr = struct.unpack("<H", b[0:2])[0]
    wide = hdr & 1
    ln = (hdr >> 6) & 0x3FF
    print(f"  header={hdr:#x} wide={wide} len={ln}")
    if wide:
        s = "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", b[2:2+ln*2]))
    else:
        s = b[2:2+ln].decode("latin1")
    print("  decoded:", repr(s))
