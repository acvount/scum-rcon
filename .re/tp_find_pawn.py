# 从活 PlayerRpcChannel 找玩家控制器 → 找 Pawn → 读坐标
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
CH = 0x2c8c1570ac0  # 活 PlayerRpcChannel（若重启会变，脚本内动态查）
# 动态查活的 PlayerRpcChannel
r2 = send("dumpfuncsraw")
for f in r2.get("functions", []):
    if dn(pool, f["nameId"]) == "Chat_Server_BroadcastChatMessage":
        cls = int(f["outer"]); break
cid = rdu32(cls + 0x18)
insts = send(f"findbyclassnameid {cid} 50").get("items", [])
live = None
for it in insts:
    a = int(it["addr"])
    if "Default__" in dn(pool, it["nameId"]): continue
    if struct.unpack("<Q", raw(a + 0x20, 8))[0] == 0: continue
    live = a
print("live PlayerRpcChannel:", hex(live) if live else None)
if not live:
    S.close(); raise SystemExit(1)
ctrl = struct.unpack("<Q", raw(live + 0x20, 8))[0]
ccid = rdu32(ctrl + 0x18)
print("owner(Controller?):", hex(ctrl), "class:", dn(pool, ccid))

# 在控制器内存里扫描 Pawn（UObject 指针，类名含 Character/Prisoner/Pawn）
print("--- 扫描控制器内存找 Pawn ---")
data = raw(ctrl, 0x800)
cands = []
for off in range(0, 0x800 - 8, 8):
    v = struct.unpack("<Q", data[off:off+8])[0]
    if not (0x10000 < v < 0x7FFFFFFFFFFF): continue
    try:
        vt = rd64(v)
        if not (mod <= vt < mod + 0x7F00000): continue
        cl = rd64(v + 0x10)
        if not cl: continue
        cn = dn(pool, rdu32(cl + 0x18))
        if any(k in (cn or "") for k in ("Character", "Prisoner", "Pawn", "Controller")):
            cands.append((off, v, cn))
    except Exception:
        pass
for off, v, cn in cands:
    print(f"  +{off:#05x} -> {v:#x} class={cn!r}")
S.close()
