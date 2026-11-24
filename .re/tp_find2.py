# 通过 Chat 函数的 Outer 反查控制器类，再找实例
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

st = send("stat"); pool = int(st["names"], 16)
r2 = send("dumpfuncsraw")
print("total functions:", r2.get("count"))
classAddr = None
fnAddr = None
for f in r2.get("functions", []):
    nm = dn(pool, f["nameId"])
    if nm in ("Chat_Server_BroadcastChatMessage", "Chat_Server_ProcessAdminCommand", "BroadcastChatLine"):
        a = int(f["addr"])
        outer = int(f["outer"])
        cid = rdu32(outer + 0x18)
        print(f"{nm}: fn={a:#x} outer={outer:#x} className={dn(pool, cid)!r}")
        if nm == "Chat_Server_BroadcastChatMessage":
            classAddr = outer; fnAddr = a
if not classAddr:
    print("Chat 函数不存在——类未加载")
    S.close(); raise SystemExit(1)
cid = rdu32(classAddr + 0x18)
print("class:", hex(classAddr), "id:", cid, dn(pool, cid))
r3 = send(f"findbyclassnameid {cid} 50")
print("instances:", r3.get("count"))
for it in r3.get("items", []):
    a = int(it["addr"])
    b = raw(a, 0x30)
    flags = struct.unpack("<I", b[8:12])[0]
    outer = struct.unpack("<Q", b[0x20:0x28])[0]
    print(f"  i={it['i']} addr={a:#x} flags={flags:#x} name={dn(pool,it['nameId'])!r} outer={outer:#x} outerName={dn(pool, rdu32(outer+0x18)) if outer else ''!r}")
S.close()
