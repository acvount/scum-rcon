import json, socket, re
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
print("=== ResolveObjectInternal (0x2e3ba80) 前 0x2C0 字节，rcx 相对访问 ===")
code = raw(0x7ff76de3ba80, 0x2C0)
pat = re.compile(r'\[rcx( [+-] 0x[0-9a-f]+)?\]')
for m in md.disasm(code, 0x7ff76de3ba80):
    s = f"  {m.address:#x}: {m.mnemonic} {m.op_str}"
    if pat.search(m.op_str):
        print(s)
