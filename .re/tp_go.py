# 最终传送：读 Pawn 坐标 → 随机偏移 → K2_TeleportTo(ctx=pawn)
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

# 1) 动态定位：RPC 通道 -> 控制器 -> Pawn
chatcls = None; tel = None
for f in send("dumpfuncsraw").get("functions", []):
    nm = dn(pool, f["nameId"])
    if nm == "Chat_Server_BroadcastChatMessage": chatcls = int(f["outer"])
    if nm == "K2_TeleportTo": tel = int(f["addr"])
cid = rdu32(chatcls + 0x18)
live = None
for it in send(f"findbyclassnameid {cid} 50").get("items", []):
    a = int(it["addr"])
    if "Default__" in dn(pool, it["nameId"]): continue
    if struct.unpack("<Q", raw(a + 0x20, 8))[0] == 0: continue
    live = a
ctrl = struct.unpack("<Q", raw(live + 0x20, 8))[0]
pawn = None
data = raw(ctrl, 0x800)
for off in range(0, 0x800 - 8, 8):
    v = struct.unpack("<Q", data[off:off+8])[0]
    if not (0x10000 < v < 0x7FFFFFFFFFFF): continue
    try:
        vt = rd64(v)
        if not (mod <= vt < mod + 0x7F000000): continue
        cl = rd64(v + 0x10)
        if not cl: continue
        if dn(pool, rdu32(cl + 0x18)) == "BP_Prisoner_C":
            pawn = v; break
    except Exception:
        pass
print("controller:", hex(ctrl), "pawn:", hex(pawn) if pawn else None)
if not pawn:
    S.close(); raise SystemExit(1)

# 2) 读当前坐标（RootComponent@+0x130 -> ComponentLocation@+0x1D0）
root = rd64(pawn + 0x130)
cur = struct.unpack("<3f", raw(root + 0x1D0, 12))
print("current:", cur)

# 3) 随机偏移 ±40~120 米
ang = random.uniform(0, 2 * math.pi)
dist = random.uniform(40, 120) * 100.0
nx = cur[0] + math.cos(ang) * dist
ny = cur[1] + math.sin(ang) * dist
nz = cur[2] + 120.0
print("target:", (round(nx, 1), round(ny, 1), round(nz, 1)), "fn:", hex(tel))
r = send(f"gtcall 0x{tel:x} 0x{pawn:x} 0:v:{nx:.1f},{ny:.1f},{nz:.1f} 12:r:0,0,0 24:b:0")
print("teleport:", json.dumps(r))
# 4) 复查坐标
try:
    cur2 = struct.unpack("<3f", raw(root + 0x1D0, 12))
    print("after:", cur2)
except Exception as e:
    print("recheck fail:", e)
S.close()
