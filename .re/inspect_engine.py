# inspect GameEngine UClass object + CDO + classes aggregation
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
    r = send(f"raw {a:x} {ln}"); return bytes.fromhex(r["hex"])

def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]

st = send("stat"); gob = int(st["gobjects"], 16)
chunk0 = rd64(gob + 0x10)  # FUObjectArray.ObjObjects.Objects[0] (chunk ptr array)
cls_obj = rd64(chunk0 + 2314 * 0x18)
print("UClass obj:", hex(cls_obj))
print("vtable:", hex(rd64(cls_obj)))
cdo = rd64(cls_obj + 0x118)
print("CDO@0x118:", hex(cdo))
if cdo:
    try:
        print("CDO vtable:", hex(rd64(cdo)))
        print("CDO classPtr@0x10:", hex(rd64(cdo + 0x10)))
        print("CDO outer@0x20:", hex(rd64(cdo + 0x20)))
    except Exception as e:
        print("CDO read err:", e)
r = send("classes 3000")
for c in r.get("classes", []):
    if "Engine" in c["name"] or c["name"] in ("GameEngine",):
        print("class:", c["name"], "count:", c["count"])
