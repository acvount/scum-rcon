# 精确获取 UFunction 地址，确认 ChildProperties 偏移，并遍历属性链
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

st = send("stat"); gob = int(st["gobjects"], 16)
arr = rd64(gob + 0x10); chunk0 = rd64(arr)
def obj_addr(i): return rd64(chunk0 + i * 0x18)

r = send('findobj LoadClassAsset_Blocking 20')
print("findobj:", json.dumps(r["items"], indent=1))
for it in r["items"]:
    if it["class"] != "Function":
        continue
    idx = it["i"]
    a = obj_addr(idx)
    print(f"=== UFunction idx={idx} addr={a:#x} ===")
    b = raw(a, 0x70)
    for off in range(0x40, 0x70, 8):
        v = struct.unpack("<Q", b[off:off+8])[0]
        print(f"  +{off:02x}: {v:#018x}")
    # 遍历候选 ChildProperties 偏移
    for coff in (0x48, 0x50):
        cp = struct.unpack("<Q", b[coff:coff+8])[0]
        print(f"  -- ChildProperties@{coff:#x}: {cp:#x}")
        if 0x10000 < cp < 0x7FFFFFFFFFFF:
            try:
                pb = raw(cp, 0x60)
                print("     bytes:", pb.hex(" "))
                # 尝试各偏移解码名字
                for noff in (0x18, 0x20, 0x28):
                    fid = struct.unpack("<I", pb[noff:noff+4])[0]
                    if 1000 < fid < 20000000:
                        print(f"     +{noff:02x} u32={fid} -> '{fname(fid)}'")
                # Offset/ArrayDim/ElementSize 候选
                for o2 in (0x28, 0x2C, 0x30, 0x38, 0x3C, 0x40, 0x44):
                    v32 = struct.unpack("<I", pb[o2:o2+4])[0]
                    if v32 in (0, 40, 8, 1, 48) or 0x10000 < v32 < 0x7FFFFFFF:
                        pass
                print(f"     u32@0x38={struct.unpack('<I', pb[0x38:0x3C])[0]} u32@0x3C={struct.unpack('<I', pb[0x3C:0x40])[0]} u32@0x40={struct.unpack('<I', pb[0x40:0x44])[0]}")
            except Exception as e:
                print("     read failed", e)
