import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=240)
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
def dn(pool, nid):
    if nid <= 0: return ""
    blk = rd64(pool + 0x10 + ((nid >> 16) * 8))
    if not blk: return ""
    off = (nid & 0xFFFF) * 2
    hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if ln == 0 or ln > 512: return f"?{nid}"
    d = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", d)) if wide else d.decode("latin1")

st = send("stat"); pool = int(st["names"], 16)
print("STAT", json.dumps({k: st[k] for k in st if k in ("objects","pe_index","ready")}))
r2 = send("dumpfuncsraw")
funcs = r2.get("functions", [])
print("FUNCS_TOTAL", r2.get("count"), len(funcs))
buckets = {"teleport": [], "chat": [], "broadcast": [], "notification": [], "actorlocation": [], "inventory": []}
for f in funcs:
    nm = dn(pool, f["nameId"]); low = nm.lower()
    for key, cond in (("teleport","teleport" in low),("chat","chat" in low),
                      ("broadcast","broadcast" in low),("notification","notification" in low),
                      ("actorlocation","setactorlocation" in low),("inventory","inventory" in low)):
        if cond and len(buckets[key]) < 40: buckets[key].append(nm)
for k, v in buckets.items():
    print(f"--- {k} ({len(v)}) ---")
    for n in v: print("   ", n)
print("--- instances ---")
for cls in ("BP_ConZPlayerController_C","BP_ConZPlayerCharacter_C","BP_ConZGameMode_C"):
    r = send(f"findinst {cls} 10")
    print(cls, "count=", r.get("count"))
    for it in r.get("items", [])[:6]:
        a = int(it["addr"])
        try:
            b = raw(a, 0x28); flags = struct.unpack("<I", b[8:12])[0]; outer = struct.unpack("<Q", b[0x20:0x28])[0]
            on = dn(pool, struct.unpack("<I", raw(outer+0x18,4))[0]) if outer else ""
            print("   ", hex(a), "flags=", hex(flags), "outer=", on)
        except Exception as e:
            print("   ", hex(a), "read fail", e)
S.close()
