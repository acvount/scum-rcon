# 传送准备：找 Admin teleport 函数签名 + 玩家控制器/角色实例
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

def desc_fn(faddr, pool):
    b = raw(faddr, 0xE0)
    flags = struct.unpack("<I", b[0xB0:0xB4])[0]
    psz = struct.unpack("<H", b[0xB6:0xB8])[0]
    roff = struct.unpack("<H", b[0xB8:0xBA])[0]
    func = struct.unpack("<Q", b[0xD8:0xE0])[0]
    print(f"  flags={flags:#x} parmsSize={psz} retOff={roff:#x} Func={func:#x}")
    chain = struct.unpack("<Q", b[0x50:0x58])[0]
    cur = chain
    for k in range(12):
        if not cur: break
        pb = raw(cur, 0x60)
        nid = struct.unpack("<I", pb[0x28:0x2C])[0]
        adim = struct.unpack("<I", pb[0x38:0x3C])[0]
        esz = struct.unpack("<I", pb[0x3C:0x40])[0]
        fl = struct.unpack("<I", pb[0x40:0x44])[0]
        off = struct.unpack("<I", pb[0x4C:0x50])[0]
        print(f"    prop[{k}] {decode_name(pool, nid)!r} dim={adim} size={esz} flags={fl:#x} off={off}")
        cur = struct.unpack("<Q", pb[0x20:0x28])[0]

st = send("stat"); pool = int(st["names"], 16)
r2 = send("dumpfuncsraw")
targets = {}
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    low = nm.lower()
    if "teleport" in low or ("admin" in low and "server" in low):
        targets.setdefault(nm, []).append(int(f["addr"]))
print("=== 候选函数 ===")
for nm, addrs in sorted(targets.items()):
    print(f"{nm}: {[hex(a) for a in addrs]}")
print()
for nm, addrs in sorted(targets.items()):
    print(f"=== {nm} ({hex(addrs[0])}) ===")
    try: desc_fn(addrs[0], pool)
    except Exception as e: print("  desc fail:", e)

print("\n=== 玩家控制器/角色实例 ===")
for cls in ("BP_ConZPlayerController_C", "BP_ConZPlayerCharacter_C", "ConZPlayerController", "ConZPlayerCharacter"):
    r = send(f"findinst {cls} 10")
    print(f"{cls}: {r.get('count')}")
    for it in r.get("items", []):
        a = int(it["addr"])
        try:
            b = raw(a, 0x28)
            flags = struct.unpack("<I", b[8:12])[0]
            outer = struct.unpack("<Q", b[0x20:0x28])[0]
            on = ""
            if outer:
                on = decode_name(pool, struct.unpack("<I", raw(outer + 0x18, 4))[0])
            print(f"  i={it['i']} addr={a:#x} flags={flags:#x} outer={on!r}")
        except Exception as e:
            print("  read fail", e)
S.close()
