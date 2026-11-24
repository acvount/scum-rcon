# 读 LoadClassAsset_Blocking 的两个子属性对象原始字节，用 fname 解码候选名字字段
import json, socket, struct
def send(cmd, timeout=60):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def rd32(a): return struct.unpack("<I", raw(a, 4))[0]
def fname(i):
    r = send(f"fname {i}")
    return r.get("name", "?")

r = send('dumpobj LoadClassAsset_Blocking 224')
obj = bytes.fromhex(r["items"][0]["hex"])
child = struct.unpack("<Q", obj[0x50:0x58])[0]
print("child0:", hex(child))
for k in range(2):
    c = child if k == 0 else struct.unpack("<Q", obj[0x50:0x58])[0]
    if k == 1:
        c = rd64(c + 0x10)  # Next@0x10 猜测
    print(f"=== child{k} @ {c:#x} ===")
    b = raw(c, 0x60)
    print("bytes:", b.hex(" "))
    # 在 0x08..0x30 找看起来像 FName id 的 u32 并解码
    for off in range(0x08, 0x30, 4):
        v = struct.unpack("<I", b[off:off+4])[0]
        if 1000 < v < 20000000:
            nm = fname(v)
            if nm and nm != "?" and len(nm) < 60:
                print(f"  +{off:02x}: u32={v} -> '{nm}'")
