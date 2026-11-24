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
print("=== 0x7ff76de40b52..0x7ff76de40c20 (copy path) ===")
code = raw(0x7ff76de40b52, 0xD0)
for m in md.disasm(code, 0x7ff76de40b52):
    print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
