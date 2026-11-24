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

def obj_addr(idx):
    st = send("stat"); gob = int(st["gobjects"], 16)
    chunk0 = rd64(rd64(gob + 0x10))
    return rd64(chunk0 + idx * 0x18)

for label, addr in [("GameMode classPtr", 0x23B37B66000), ("PlayerController classPtr", 0x23B355A5000)]:
    print(f"=== {label} @ {addr:#x} ===")
    try:
        b = raw(addr, 0x30)
        print("  bytes:", b.hex(" "))
        print("  vtable:", hex(struct.unpack('<Q', b[0:8])[0]))
        print("  flags:", hex(struct.unpack('<I', b[8:12])[0]), "index:", struct.unpack('<I', b[12:16])[0])
        print("  class:", hex(struct.unpack('<Q', b[0x10:0x18])[0]))
        print("  name FName:", struct.unpack('<II', b[0x18:0x20]))
        print("  outer:", hex(struct.unpack('<Q', b[0x20:0x28])[0]))
    except Exception as e:
        print("  read failed:", e)

# GameMode class object current index → address
r = send('findobj ConZGameMode 10')
print("findobj ConZGameMode:", json.dumps(r["items"], indent=1))
