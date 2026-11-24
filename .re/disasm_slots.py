# disasm candidates slots 78..92 of UGameEngine vtable (first 48 bytes each)
import json, socket, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

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
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])

def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]

md = Cs(CS_ARCH_X86, CS_MODE_64)
st = send("stat"); gob = int(st["gobjects"], 16)
arr = rd64(gob + 0x10); chunk0 = rd64(arr)
def obj_at(i): return rd64(chunk0 + i * 0x18)
# GameEngine UClass at index 2314 (from findobj)
cls_obj = obj_at(2314)
cdo = rd64(cls_obj + 0x118)
cvt = rd64(cdo)
base = int(st["module"], 16)
print(f"CDO={cdo:#x} vt={cvt:#x} base={base:#x}")
slots = {}
for i in range(78, 96):
    f = rd64(cvt + i * 8)
    slots[i] = f
    try:
        code = raw(f, 48)
    except Exception as e:
        print(f"[{i}] {f:#x} rva={(f-base):#x} unreadable")
        continue
    insns = list(md.disasm(code, f))
    first = " ; ".join(f"{m.mnemonic} {m.op_str}".strip() for m in insns[:6])
    print(f"[{i}] {f:#x} rva={(f-base):#x} | {first}")
print()
# also check prologue safety: does any instruction cross byte 14?
for i, f in slots.items():
    code = raw(f, 32)
    insns = list(md.disasm(code, f))
    ok = True
    for m in insns:
        if m.address - f < 14 < m.address - f + m.size:
            ok = False
    print(f"slot {i}: 14-byte patch safe = {ok}  ({insns[0].mnemonic} {insns[0].op_str}, {insns[0].size}B)")
