# 传送工具：定位玩家控制器/角色 → 读坐标 → 随机传送
import json, socket, struct, sys, random, time

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
print("objects:", st["objects"])

pr = send("tickprobe 87 19 2500")
tid = pr["tids"][0] if pr.get("tids") else 0
print("tid:", tid)
r = send(f'gtload "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C" 86 14 {tid} GameEngine 1')
cp = int(r["classPtr"]) if r.get("classPtr") else 0
print("gtload:", r.get("fired"), "ex:", r.get("ex"), "classPtr:", hex(cp) if cp else 0)
if not cp:
    # 从对象表找类对象：按名字 id（host 解码枚举）太重，先退出
    print("classPtr=0 —— 玩家尚未上线或类未加载")
    S.close(); raise SystemExit(1)
cid = rdu32(cp + 0x18)  # 类名 id
print("class name id:", cid, "->", dn(pool, cid))

r2 = send(f"findbyclassnameid {cid} 50")
insts = r2.get("items", [])
print("instances:", r2.get("count"))
for it in insts:
    a = int(it["addr"])
    nid = it["nameId"]
    b = raw(a, 0x28)
    flags = struct.unpack("<I", b[8:12])[0]
    outer = struct.unpack("<Q", b[0x20:0x28])[0]
    print(f"  i={it['i']} addr={a:#x} flags={flags:#x} name={dn(pool,nid)!r} outer={outer:#x}")
S.close()
