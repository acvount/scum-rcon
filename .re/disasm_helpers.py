import json, socket, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
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
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
for name, addr in [("Step(0x6e140af0)", 0x7ff76de40af0), ("FallbackCopy(0x6e140b20)", 0x7ff76de40b20)]:
    print(f"=== {name} ===")
    code = raw(addr, 128)
    for m in md.disasm(code, addr):
        print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
        if m.mnemonic in ("ret",) and m.address > addr + 40:
            break
