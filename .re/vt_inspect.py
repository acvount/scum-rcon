# vt_inspect.py — 通过 harness raw 命令读对象内存，定位 UGameEngine CDO 的 vtable 槽位
import json, socket, struct, sys

HOST, PORT = "127.0.0.1", 17880

def send(cmd):
    with socket.create_connection((HOST, PORT), timeout=60) as s:
        s.sendall((cmd + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

def raw(addr, ln):
    r = send(f"raw {addr:x} {ln}")
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])

def rd64(a):
    return struct.unpack("<Q", raw(a, 8))[0]

def find(name, cls=None, mx=100):
    r = send(f'findobj "{name}" {mx}')
    out = []
    for it in r.get("items", []):
        if cls is None or it["class"] == cls:
            out.append(it)
    return out

def obj_addr(gobjects, idx):
    # FUObjectArray@0x00: ObjFirstGCIndex(4)+ObjLastNonGCIndex(4)+Max(4)+Open(4)=16
    # FChunkedFixedUObjectArray@0x10: Objects@0x00(8), PreAllocated@0x08(8)
    chunk0 = rd64(gobjects + 0x10 + 0x08)
    return rd64(chunk0 + idx * 0x18)

def main():
    st = send("stat")
    gob = int(st["gobjects"], 16)
    print("gobjects:", hex(gob))
    hits = find("Default__GameEngine")
    print("Default__GameEngine hits:", json.dumps(hits, indent=1))
    if not hits:
        hits = find("GameEngine")
        print("GameEngine hits:", json.dumps(hits, indent=1))
        return
    idx = hits[0]["i"]
    cls_obj = obj_addr(gob, idx)
    print("UClass obj:", hex(cls_obj))
    # UClass::ClassDefaultObject @ +0x118
    cdo = rd64(cls_obj + 0x118)
    print("CDO:", hex(cdo))
    vt = rd64(cdo)
    print("vtable:", hex(vt))
    slots = {}
    end = 0
    for i in range(0, 200):
        try:
            f = rd64(vt + i * 8)
        except Exception as e:
            end = i
            break
        slots[i] = f
    print("vtable readable slots: 0..%d" % (end - 1 if end else 199))
    lo, hi = 60, 120
    print("=== slots %d..%d ===" % (lo, hi))
    for i in range(lo, hi):
        f = slots.get(i)
        if not f: continue
        hx = raw(f, 24).hex(" ")
        print("%3d  %s  %s" % (i, hex(f), hx))

if __name__ == "__main__":
    main()
