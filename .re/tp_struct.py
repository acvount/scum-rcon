# 解析 Admin_Server_TeleportTo_Location 的 TeleportRequest 结构体布局
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
def rd64(a):
    return struct.unpack("<Q", raw(a, 8))[0]
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

st = send("stat"); pool = int(st["names"], 16)
r2 = send("dumpfuncsraw")
addr = None
for f in r2.get("functions", []):
    if dn(pool, f["nameId"]) == "Admin_Server_TeleportTo_Location":
        addr = int(f["addr"]); break
print("fn:", hex(addr) if addr else None)
b = raw(addr, 0xE0)
chain = struct.unpack("<Q", b[0x50:0x58])[0]
cur = chain
props = []
for k in range(8):
    if not cur: break
    pb = raw(cur, 0x70)
    nid = struct.unpack("<I", pb[0x28:0x2C])[0]
    esz = struct.unpack("<I", pb[0x3C:0x40])[0]
    fl = struct.unpack("<I", pb[0x40:0x44])[0]
    off = struct.unpack("<I", pb[0x4C:0x50])[0]
    print(f"prop[{k}] {dn(pool,nid)!r} size={esz} flags={fl:#x} off={off}")
    props.append((cur, dn(pool, nid), esz, off))
    cur = struct.unpack("<Q", pb[0x20:0x28])[0]

# 取 TeleportRequest 属性，找 Struct 指针（FStructProperty::Struct）
for paddr, pname, psz, poff in props:
    if pname != "TeleportRequest": continue
    pb = raw(paddr, 0x90)
    print("\nTeleportRequest prop bytes:")
    for off in range(0, 0x90, 8):
        v = struct.unpack("<Q", pb[off:off+8])[0]
        print(f"  +{off:#04x}: {v:#x}")
    # 猜 Struct 指针：指向 UObject 且其类名为 ScriptStruct/Class
    for off in range(0x08, 0x90, 8):
        v = struct.unpack("<Q", pb[off:off+8])[0]
        if not (0x10000 < v < 0x7FFFFFFFFFFF): continue
        try:
            vt = rd64(v)
            if not (0x7FF000000000 <= vt < 0x800000000000): continue
            cls = rd64(v + 0x10)
            if not cls: continue
            cnid = struct.unpack("<I", raw(cls + 0x18, 4))[0]
            cn = dn(pool, cnid)
            if "Struct" in cn or "Class" in cn:
                # 读它的 ChildProperties (+0x50) 并走链
                st_ptr = v
                print(f"\n== 疑似 Struct 指针 @+{off:#x} -> {v:#x} class={cn!r} ==")
                cp = rd64(st_ptr + 0x50)
                c2 = cp
                for k2 in range(12):
                    if not c2: break
                    qb = raw(c2, 0x60)
                    nid2 = struct.unpack("<I", qb[0x28:0x2C])[0]
                    esz2 = struct.unpack("<I", qb[0x3C:0x40])[0]
                    off2 = struct.unpack("<I", qb[0x4C:0x50])[0]
                    fl2 = struct.unpack("<I", qb[0x40:0x44])[0]
                    print(f"   field {dn(pool,nid2)!r} size={esz2} flags={fl2:#x} off={off2}")
                    c2 = struct.unpack("<Q", qb[0x20:0x28])[0]
        except Exception:
            pass
S.close()
