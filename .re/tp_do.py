# 传送执行：读 Pawn 坐标 → 随机偏移 → K2_TeleportTo
import json, socket, struct, random, math
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

# 1) 定位活 RPC 通道 -> 控制器 -> Pawn
r2 = send("dumpfuncsraw")
chatcls = None
targets = {}
for f in r2.get("functions", []):
    nm = dn(pool, f["nameId"])
    if nm == "Chat_Server_BroadcastChatMessage":
        chatcls = int(f["outer"])
    if nm in ("K2_GetActorLocation", "K2_TeleportTo"):
        targets[nm] = int(f["addr"])
cid = rdu32(chatcls + 0x18)
live = None
for it in send(f"findbyclassnameid {cid} 50").get("items", []):
    a = int(it["addr"])
    if "Default__" in dn(pool, it["nameId"]): continue
    if struct.unpack("<Q", raw(a + 0x20, 8))[0] == 0: continue
    live = a
ctrl = struct.unpack("<Q", raw(live + 0x20, 8))[0]
print("controller:", hex(ctrl), dn(pool, rdu32(ctrl + 0x18)))
data = raw(ctrl, 0x800)
pawn = None
for off in range(0, 0x800 - 8, 8):
    v = struct.unpack("<Q", data[off:off+8])[0]
    if not (0x10000 < v < 0x7FFFFFFFFFFF): continue
    try:
        vt = rd64(v)
        if not (mod <= vt < mod + 0x7F00000): continue
        cl = rd64(v + 0x10)
        if not cl: continue
        cn = dn(pool, rdu32(cl + 0x18))
        if cn == "BP_Prisoner_C":
            pawn = v; break
    except Exception:
        pass
print("pawn:", hex(pawn) if pawn else None)
if not pawn:
    S.close(); raise SystemExit(1)

# 2) 读当前坐标：K2_GetActorLocation(Actor=pawn)，ctx=pawn
gl = targets.get("K2_GetActorLocation")
print("K2_GetActorLocation:", hex(gl))
c1 = send(f"gtcallpe 0x{gl:x} o:0x{pawn:x} 0:o:0x{pawn:x}")
print("getloc:", json.dumps(c1))
gp = send("gtparms")
floats = gp.get("floats", [])
print("floats[:8]:", floats[:8])
# 返回 FVector 在 parms+8（retOff）→ floats[2..5]
cur = (floats[2], floats[3], floats[4]) if len(floats) > 4 else None
print("current location:", cur)

# 3) 随机偏移（±120 米），高度 +150cm
if cur and all(abs(v) < 5e6 for v in cur):
    ang = random.uniform(0, 2*math.pi)
    dist = random.uniform(40.0, 120.0) * 100.0  # cm
    nx = cur[0] + math.cos(ang) * dist
    ny = cur[1] + math.sin(ang) * dist
    nz = cur[2] + 150.0
    tgt = (nx, ny, nz)
    print("target location:", tgt)
    tel = targets.get("K2_TeleportTo")
    print("K2_TeleportTo:", hex(tel))
    c2 = send(f"gtcallpe 0x{tel:x} o:0x{pawn:x} 0:v:{nx:.1f},{ny:.1f},{nz:.1f} 12:r:0,0,0 24:b:0")
    print("teleport:", json.dumps(c2))
else:
    print("坐标异常，放弃传送")
S.close()
