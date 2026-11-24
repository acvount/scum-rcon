import json, socket, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
def send(cmd):
    with socket.create_connection(("127.0.0.1", 17880), timeout=90) as s:
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

# find engine-named objects (not just class objects)
r = send("findobj Engine 300")
print("=== findobj Engine ===")
for it in r.get("items", []):
    print(f"  i={it['i']} name={it['name']} class={it['class']}")
r2 = send("findobj Engine 3000")
print("total engine-name matches:", r2.get("count"))

# disasm thunk target 0x7ff76b9a5be0
tgt = 0x7ff76b9a5be0
code = raw(tgt, 64)
print("=== thunk target 0x9975BE0 ===")
for m in md.disasm(code, tgt):
    print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
    if m.mnemonic in ("ret", "jmp"): break

# also disasm 0x7ff76b9218b0 (the repeated slot addr) and 0x7ff76b923160
for t, label in ((0x7ff76b9218b0, "repeat-stub 0x91218B0"), (0x7ff76b923160, "stub 0x9123160")):
    print(f"=== {label} ===")
    try:
        c2 = raw(t, 24)
        for m in md.disasm(c2, t):
            print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
    except Exception as e:
        print("  read failed", e)
