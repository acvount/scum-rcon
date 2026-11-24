import json, socket
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
for name, addr, ln in [("resolve? (RVA 0x96f3c0)", 0x7ff76b97f3c0, 0x80), ("check? (RVA 0x2cae000)", 0x7ff76dcbe000, 0x60)]:
    print(f"=== {name} ===")
    code = raw(addr, ln)
    for m in md.disasm(code, addr):
        print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
