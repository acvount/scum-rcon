# 解析分发函数里的 RIP 相对引用，还原两条分支各引用了哪些字符串
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
data = open(EXE, "rb").read()
e = struct.unpack_from("<I", data, 0x3C)[0]
ns = struct.unpack_from("<H", data, e + 6)[0]
osz = struct.unpack_from("<H", data, e + 20)[0]
secs = []
o = e + 24 + osz
for i in range(ns):
    p = o + i * 40
    vs, va, rs, ra = struct.unpack_from("<IIII", data, p + 8)
    secs.append((va, vs, ra, rs))

def rva2off(rva):
    for va, vs, ra, rs in secs:
        if va <= rva < va + max(vs, rs):
            return ra + (rva - va)
    return None

def read_str_utf16(va, maxlen=120):
    off = rva2off(va)
    if off is None:
        return None
    raw = data[off:off + maxlen * 2]
    try:
        s = raw.decode("utf-16-le")
    except Exception:
        return None
    end = s.find("\x00")
    if end >= 0:
        s = s[:end]
    if not s or any(ord(c) < 32 or ord(c) > 126 for c in s):
        return None
    return s

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
START, LEN = 0x1F4FED0, 0x900
off = rva2off(START)
code = data[off:off + LEN]
insns = list(md.disasm(code, START))

print("RIP 相对引用的字符串（按地址顺序）：")
refs = {}
for m in insns:
    if not m.operands:
        continue
    for op in m.operands:
        if op.type == 3 and op.mem.base == 0x29:  # X86_OP_MEM, RIP
            target = m.address + m.size + op.mem.disp
            if target in refs:
                continue
            s = read_str_utf16(target)
            refs[target] = s
for addr in sorted(refs):
    s = refs[addr]
    print(f"  {addr:#x}  {s!r}")

print("\n关键分支点上下文：")
for m in insns:
    if m.address in (0x1F4FF8C, 0x1F4FF8F, 0x1F4FF95, 0x1F5005B, 0x1F5012B):
        print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
