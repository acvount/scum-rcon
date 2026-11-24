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
    if not r.get("ok"): raise RuntimeError(f"raw {a:#x} fail")
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

# 动态取函数地址（十进制字符串）
want = {"Chat_Server_BroadcastChatMessage", "Chat_Server_ProcessAdminCommand",
        "BroadcastChatLine", "SendChatLineToPlayer", "Multicast_ShowEventNotification"}
addrs = {}
r2 = send("dumpfuncsraw")
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    if nm in want:
        addrs[nm] = int(f["addr"])

def desc_fn(faddr, label):
    b = raw(faddr, 0xE0)
    flags = struct.unpack("<I", b[0xB0:0xB4])[0]
    psz = struct.unpack("<H", b[0xB6:0xB8])[0]
    roff = struct.unpack("<H", b[0xB8:0xBA])[0]
    func = struct.unpack("<Q", b[0xD8:0xE0])[0]
    print(f"=== {label} ({faddr:#x}) flags={flags:#x} parmsSize={psz} retOff={roff:#x} Func={func:#x} native={bool(flags & 0x400)} ===")
    chain = struct.unpack("<Q", b[0x50:0x58])[0]
    cur = chain
    for k in range(12):
        if not cur: break
        pb = raw(cur, 0x60)
        nid = struct.unpack("<I", pb[0x28:0x2C])[0]
        nnum = struct.unpack("<I", pb[0x2C:0x30])[0]
        adim = struct.unpack("<I", pb[0x38:0x3C])[0]
        esz = struct.unpack("<I", pb[0x3C:0x40])[0]
        fl = struct.unpack("<I", pb[0x40:0x44])[0]
        off = struct.unpack("<I", pb[0x4C:0x50])[0]
        nm = decode_name(pool, nid)
        print(f"  prop[{k}] @{cur:#x} name={nm!r} num={nnum} arrayDim={adim} elemSize={esz} flags={fl:#x} offset={off}")
        cur = struct.unpack("<Q", pb[0x20:0x28])[0]

for label in sorted(want):
    if label in addrs:
        try:
            desc_fn(addrs[label], label)
        except Exception as e:
            print(f"{label}: {e}")
    else:
        print(f"{label}: NOT FOUND")
S.close()
