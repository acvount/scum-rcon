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
    if not r.get("ok"): raise RuntimeError(f"raw fail {a:#x}: {r}")
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def fname(i):
    r = send(f"fname {i}")
    return r.get("name", "?")

r = send('findobj LoadClassAsset_Blocking 5')
idx = [it["i"] for it in r["items"] if it["class"] == "Function"][0]
st = send("stat"); gob = int(st["gobjects"], 16)
chunk0 = rd64(rd64(gob + 0x10))
fn = rd64(chunk0 + idx * 0x18)
print("UFunction:", hex(fn))
chain = rd64(fn + 0x50)
print("child0:", hex(chain))
b0 = raw(chain, 0x60)
print("child0 bytes:", b0.hex(" "))
print("child0+0x18 u64:", hex(struct.unpack('<Q', b0[0x18:0x20])[0]))
print("child0+0x20 u64:", hex(struct.unpack('<Q', b0[0x20:0x28])[0]))
print("child0+0x28 u64:", hex(struct.unpack('<Q', b0[0x28:0x30])[0]))
print("child0+0x4C u32:", struct.unpack('<I', b0[0x4C:0x50])[0])
print("child0+0x40 u32:", hex(struct.unpack('<I', b0[0x40:0x44])[0]))
nxt = struct.unpack('<Q', b0[0x20:0x28])[0]
print("=== candidate 'next' @+0x20:", hex(nxt), "===")
try:
    b1 = raw(nxt, 0x60)
    print("bytes:", b1.hex(" "))
    print("vtable:", hex(struct.unpack('<Q', b1[0:8])[0]))
    print("+0x4C u32:", struct.unpack('<I', b1[0x4C:0x50])[0])
    print("+0x40 u32:", hex(struct.unpack('<I', b1[0x40:0x44])[0]))
    for noff in (0x18, 0x20, 0x28):
        fid = struct.unpack("<I", b1[noff:noff+4])[0]
        if 1000 < fid < 20000000:
            print(f"  +{noff:02x} u32={fid} -> '{fname(fid)}'")
except Exception as e:
    print("read failed:", e)
