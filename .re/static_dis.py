# 静态分析：PE 文件反汇编关键函数（RVA 直接映射）
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
data = open(EXE, "rb").read()

# --- 解析 PE 分段 ---
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e_lfanew:e_lfanew+4] == b"PE\0\0"
num_sec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
sections = []
sec_off = e_lfanew + 24 + opt_size
for i in range(num_sec):
    o = sec_off + i * 40
    name = data[o:o+8].rstrip(b"\0").decode("latin1", "replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", data, o + 8)
    sections.append((name, vaddr, vsize, raddr, rsize))
print("sections:")
for s in sections:
    print("  ", s)

def rva2off(rva):
    for name, va, vs, ra, rs in sections:
        if va <= rva < va + max(vs, rs):
            return ra + (rva - va)
    return None

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def disasm(rva, length):
    off = rva2off(rva)
    out = []
    for m in md.disasm(data[off:off+length], rva):
        out.append((m.address, m.mnemonic, m.op_str))
    return out

def show(title, rva, length):
    print(f"\n=== {title} (RVA {rva:#x}) ===")
    for a, mn, ops in disasm(rva, length):
        print(f"  {a:#x}: {mn} {ops}")

# 分发函数：0x1F4FED0，看 AL 分支两侧
show("dispatch head", 0x1F4FED0, 0xC0)
show("branch target A (je 0x1F5005B)", 0x1F5005B, 0x60)
show("admin check fn", 0x1F8D8C0, 0x100)
