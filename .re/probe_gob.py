# correct chain: gob+0x10 -> Objects[] array -> Objects[0] -> item[idx*0x18].Object
import json, socket, struct
def send(cmd):
    with socket.create_connection(("127.0.0.1", 17880), timeout=60) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"):
        raise RuntimeError(f"raw failed at {a:#x}: {r}")
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]

st = send("stat"); gob = int(st["gobjects"], 16)
arr = rd64(gob + 0x10)          # ObjObjects.Objects (chunk ptr array)
chunk0 = rd64(arr)              # Objects[0]
def obj_at(i):
    item = chunk0 + i * 0x18
    return rd64(item)
print("arr:", hex(arr), "chunk0:", hex(chunk0))
for i in (2314,):
    o = obj_at(i)
    print(f"obj[{i}]:", hex(o))
    vt = rd64(o)
    print("  vtable:", hex(vt))
    print("  flags@08:", hex(struct.unpack('<I', raw(o+8,4))[0]))
    print("  cls@10:", hex(rd64(o+0x10)))
    print("  name@18:", struct.unpack('<II', raw(o+0x18,8)))
    print("  outer@20:", hex(rd64(o+0x20)))
    cdo = rd64(o + 0x118)
    print("  CDO@118:", hex(cdo))
    if cdo:
        cvt = rd64(cdo)
        print("  CDO vtable:", hex(cvt))
        print("  CDO cls@10:", hex(rd64(cdo+0x10)))
        print("  CDO outer@20:", hex(rd64(cdo+0x20)))
        print("  CDO name@18:", struct.unpack('<II', raw(cdo+0x18,8)))
        # dump slots 60..120
        print("  === vtable slots 60..120 ===")
        for s in range(60, 121):
            f = rd64(cvt + s*8)
            print(f"   [{s}] {f:#x}")
