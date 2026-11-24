import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=120)
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
# outer 对象名字
for label, addr in [("outer-of-19369", 0x1DC70A88600), ("outer-of-19162", 0x1DC706FB740)]:
    b = raw(addr, 0x30)
    nid = struct.unpack("<I", b[0x18:0x1C])[0]
    cls = struct.unpack("<Q", b[0x10:0x18])[0]
    cnid = struct.unpack("<I", raw(cls + 0x18, 4))[0] if cls else 0
    print(f"{label}: addr={addr:#x} name={decode_name(pool, nid)!r} class={decode_name(pool, cnid)!r}")
# UFunction 头
for label, faddr in [("BroadcastChatLine", 0x1DC7A632D0), ("SendChatLineToPlayer", 0x1DC7A63A30),
                     ("Chat_Server_BroadcastChatMessage", 0x1DC7A64A50), ("Chat_Server_ProcessAdminCommand", 0x1DC7A64C70),
                     ("Multicast_ShowEventNotification", 0x1DC7A64D90)]:
    try:
        b = raw(faddr, 0xE0)
    except Exception as e:
        print(f"{label}: read fail {e}")
        continue
    flags = struct.unpack("<I", b[0xB0:0xB4])[0]
    nump = b[0xB4]
    psz = struct.unpack("<H", b[0xB6:0xB8])[0]
    roff = struct.unpack("<H", b[0xB8:0xBA])[0]
    func = struct.unpack("<Q", b[0xD8:0xE0])[0]
    print(f"{label}: flags={flags:#x} numParms={nump} parmsSize={psz} retOff={roff:#x} Func={func:#x} native={bool(flags & 0x400)}")
S.close()
