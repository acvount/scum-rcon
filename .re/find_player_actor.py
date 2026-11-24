# 通过 PersistentLevel 枚举 actor，找玩家控制器/角色实例
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
# 找 PersistentLevel
lvl = None
r = send("findobj PersistentLevel 10")
for it in r.get("items", []):
    if it["name"] == "PersistentLevel":
        d = send(f"dumpidx {it['i']}")
        lvl = int(d["addr"], 16)
        break
print("PersistentLevel:", hex(lvl) if lvl else None)
if not lvl:
    S.close(); raise SystemExit

r2 = send(f"findbyouter {lvl:x} 4000")
print("children:", r2.get("count"))
hits = []
for it in r2.get("items", []):
    nm = decode_name(pool, it["nameId"])
    cls = it.get("class") or ""
    low = (nm + " " + cls).lower()
    if any(k in low for k in ("playercontroller", "playercharacter", "controller", "character", "prisoner", "pawn")):
        hits.append((it["i"], it["addr"], nm, cls))
print("hits:", len(hits))
for h in hits[:40]:
    print(f"  i={h[0]} addr={h[1]} name={h[2]!r} class={h[3]!r}")
S.close()
