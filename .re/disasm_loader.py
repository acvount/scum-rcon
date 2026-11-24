# 反汇编 LoadClassAsset_Blocking 的 native 实现 + 读 FSoftClassPtrProperty 元数据
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
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def rd32(a): return struct.unpack("<I", raw(a, 4))[0]

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

r = send('dumpobj LoadClassAsset_Blocking 224')
obj = bytes.fromhex(r["items"][0]["hex"])
func = struct.unpack("<Q", obj[0xD8:0xE0])[0]
child = struct.unpack("<Q", obj[0x50:0x58])[0]
print("func:", hex(func), " childProps:", hex(child))
print("prop Name@18:", hex(rd32(child+0x18)))
print("prop ElementSize@2C:", rd32(child+0x2C))
print("prop Offset@3C:", rd32(child+0x3C))
print("prop ArrayDim@28:", rd32(child+0x28))
print("prop flags@30:", hex(rd64(child+0x30)))
print("=== disasm exec (first 96 bytes) ===")
code = raw(func, 96)
for m in md.disasm(code, func):
    print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
print("=== disasm exec cont (96..320) ===")
code2 = raw(func + 96, 224)
for m in md.disasm(code2, func + 96):
    print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
