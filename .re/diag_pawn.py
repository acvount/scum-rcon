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
def rdu32(a): return struct.unpack("<I", raw(a, 4))[0]
def dn(pool, nid):
    if nid <= 0: return ""
    try:
        blk = rd64(pool + 0x10 + ((nid >> 16) * 8))
        if not blk: return ""
        off = (nid & 0xFFFF) * 2
        hdr = struct.unpack("<H", raw(blk + off, 2))[0]
        wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
        if ln == 0 or ln > 512: return f"?{nid}"
        d = raw(blk + off + 2, ln * (2 if wide else 1))
        return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", d)) if wide else d.decode("latin1")
    except Exception:
        return f"?{nid}"

st = send("stat"); pool = int(st["names"], 16); mod = int(st["module"], 16)
fn = None; cls = None
for f in send("dumpfuncsraw").get("functions", []):
    if dn(pool, f["nameId"]) == "Chat_Server_ProcessAdminCommand":
        fn = int(f["addr"]); cls = int(f["outer"]); break
print("fn:", hex(fn) if fn else None, "cls:", hex(cls) if cls else None)
cid = rdu32(cls + 0x18)
print("class:", dn(pool, cid), "id:", cid)
insts = send(f"findbyclassnameid {cid} 50").get("items", [])
print("instances:", len(insts))
for it in insts:
    a = int(it["addr"])
    nm = dn(pool, it["nameId"])
    try:
        outer = struct.unpack("<Q", raw(a + 0x20, 8))[0]
    except Exception:
        outer = 0
    onm = dn(pool, rdu32(outer + 0x18)) if outer else ""
    print(f"  i={it['i']} addr={a:#x} name={nm!r} outer={outer:#x} outerName={onm!r}")
# 找外面是 controller 的那个
live = None
for it in insts:
    a = int(it["addr"])
    if "Default__" in dn(pool, it["nameId"]): continue
    try:
        outer = struct.unpack("<Q", raw(a + 0x20, 8))[0]
        onm = dn(pool, rdu32(outer + 0x18)) if outer else ""
    except Exception:
        continue
    if "PlayerController" in (onm or ""):
        live = a
        print("live channel:", hex(a), "owner:", hex(outer), onm)
        break
if not live:
    print("no live channel with PlayerController owner")
    S.close(); raise SystemExit(0)
ctrl = struct.unpack("<Q", raw(live + 0x20, 8))[0]
data = raw(ctrl, 0x2000)
print("--- 扫描控制器 0x2000 找角色 ---")
for off in range(0, 0x2000 - 8, 8):
    v = struct.unpack("<Q", data[off:off+8])[0]
    if not (0x10000 < v < 0x7FFFFFFFFFFF): continue
    try:
        vt = rd64(v)
        if not (mod <= vt < mod + 0x7F000000): continue
        cl = rd64(v + 0x10)
        if not cl: continue
        cn = dn(pool, rdu32(cl + 0x18))
        if any(k in (cn or "") for k in ("Prisoner", "Character", "Pawn")):
            print(f"  +{off:#06x} -> {v:#x} class={cn!r}")
    except Exception:
        pass
S.close()
