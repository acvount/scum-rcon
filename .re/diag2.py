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
fn = cls = None
for f in send("dumpfuncsraw").get("functions", []):
    if dn(pool, f["nameId"]) == "Chat_Server_ProcessAdminCommand":
        fn = int(f["addr"]); cls = int(f["outer"]); break
cid = rdu32(cls + 0x18)
insts = send(f"findbyclassnameid {cid} 50").get("items", [])
print("channels:", len(insts))
chs = []
for it in insts:
    a = int(it["addr"])
    try:
        owner = struct.unpack("<Q", raw(a + 0x20, 8))[0]
        fl = struct.unpack("<I", raw(owner + 8, 4))[0] if owner else 0
        onm = dn(pool, rdu32(owner + 0x18)) if owner else ""
    except Exception:
        owner, fl, onm = 0, 0, ""
    print(f"  chan={a:#x} owner={owner:#x} flags={fl:#x} ownerName={onm!r}")
    if owner and not (fl & 0x10) and not onm.startswith("Default__"):
        chs.append((a, owner))
if not chs:
    print("NO live channel")
    S.close(); raise SystemExit(1)
chan, ctrl = chs[-1]
print("use channel:", hex(chan), "controller:", hex(ctrl), dn(pool, rdu32(ctrl + 0x18)))
buf = b""
for start in range(0, 0x800, 0x200):
    try:
        buf += raw(ctrl + start, 0x200)
    except Exception as e:
        print("chunk fail", hex(start), e)
        break
print("controller bytes:", len(buf))
for off in range(0, len(buf) - 8, 8):
    v = struct.unpack("<Q", buf[off:off+8])[0]
    if not (0x10000 < v < 0x7FFFFFFFFFFF): continue
    try:
        vt = rd64(v)
        if not (mod <= vt < mod + 0x7F000000): continue
        cl = rd64(v + 0x10)
        cn = dn(pool, rdu32(cl + 0x18)) if cl else ""
        loc = None
        try:
            root = rd64(v + 0x130)
            if 0x10000 < root < 0x7FFFFFFFFFFF:
                loc = struct.unpack("<3f", raw(root + 0x1D0, 12))
        except Exception:
            pass
        if cn and (abs(loc[0]) < 2e6 if loc else True):
            print(f"  +{off:#05x} {v:#x} class={cn!r} loc={loc}")
    except Exception:
        pass
S.close()
