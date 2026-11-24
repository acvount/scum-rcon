# 完整链条：gtload → findbyouter → 主机侧解码名字
import json, socket, struct, sys
def send(cmd, timeout=120):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(1 << 20)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])

def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]

def decode_name(pool, nid):
    """用真实块数组解码名字（绕过插件解码）"""
    if nid <= 0: return ""
    block = nid >> 16
    off = (nid & 0xFFFF) * 2
    blk = rd64(pool + 0x10 + block * 8)
    if not blk: return ""
    hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    wide = hdr & 1
    ln = (hdr >> 6) & 0x3FF
    if ln == 0 or ln > 512: return ""
    data = raw(blk + off + 2, ln * (2 if wide else 1))
    if wide:
        return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", data))
    return data.decode("latin1")

st = send("stat")
pool = int(st["names"], 16)
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 0
path = "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C"
r = send(f'gtload "{path}" 86 14 {tid} GameEngine 1')
cp = int(r["classPtr"])
print("gtload fired:", r.get("fired"), "ex:", r.get("ex"), "classPtr:", hex(cp))
if not cp:
    sys.exit(1)
# 类对象本身的名字
obj = raw(cp, 0x28)
nid = struct.unpack("<I", obj[0x18:0x1C])[0]
print("class object nameId:", nid, "->", repr(decode_name(pool, nid)))
# 枚举子对象
r2 = send(f"findbyouter {cp:x} 2000")
print("children:", r2.get("count"))
kids = []
for it in r2.get("items", []):
    nm = decode_name(pool, it["nameId"])
    kids.append((it["i"], it["addr"], it["nameId"], nm, it["class"]))
chat = [k for k in kids if "Chat" in k[3] or "chat" in k[3]]
print("=== children with 'chat' in name ===")
for k in chat:
    print(f"  i={k[0]} addr={k[1]} name={k[3]!r} class={k[4]}")
print("=== all children names (first 80) ===")
for k in kids[:80]:
    print(f"  i={k[0]} name={k[3]!r} class={k[4]}")
