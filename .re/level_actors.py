import json, socket, struct
from collections import Counter
S = socket.create_connection(("127.0.0.1", 17880), timeout=300)
def send(cmd):
    S.sendall((cmd + "\n").encode()); b = b""
    while not b.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        b += c
    return json.loads(b.decode("utf-8", "replace").strip())
def raw(a, ln):
    try:
        r = send(f"raw {a:x} {ln}")
        if not r.get("ok"): return None
        return bytes.fromhex(r["hex"])
    except Exception:
        return None
def rd64(a):
    b = raw(a, 8)
    return struct.unpack("<Q", b)[0] if b else 0
def dn(pool, nid):
    if nid <= 0: return ""
    try:
        blk = rd64(pool + 0x10 + ((nid >> 16) * 8))
        if not blk: return ""
        off = (nid & 0xFFFF) * 2
        h = raw(blk + off, 2)
        if not h: return ""
        hdr = struct.unpack("<H", h)[0]
        wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
        if ln == 0 or ln > 512: return f"?{nid}"
        d = raw(blk + off + 2, ln * (2 if wide else 1))
        if not d: return f"?{nid}"
        return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", d)) if wide else d.decode("latin1")
    except Exception:
        return f"?{nid}"

st = send("stat"); pool = int(st["names"], 16)
LEVEL = 0x20639bcf7c0
r2 = send("findbyouter %x 4000" % LEVEL)
items = r2.get("items", [])
print("children:", r2.get("count"), "returned:", len(items))
classes = Counter((c.get("class") or "?") for c in items)
print("--- 类分布（前 25）---")
for cls, n in classes.most_common(25):
    print(f"  {n:5d}  {cls}")
print("--- 玩家相关实例 ---")
for c in items:
    cls = c.get("class") or ""
    low = cls.lower()
    if any(k in low for k in ("controller", "character", "pawn", "prisoner")):
        print(f"  i={c['i']} addr={c['addr']} class={cls!r} name={dn(pool, c['nameId'])!r}")
S.close()
