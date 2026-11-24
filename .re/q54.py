
import json, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
r = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\vtable.json"))
base = int(r["base"]); slots=[int(s) for s in r["slots"]]
path = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
d = open(path,'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]; coff=e+4
nsec = struct.unpack_from('<H', d, coff+2)[0]; optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff+20; sec_off = opt+optsz
secs=[]
for i in range(nsec):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((name, va, vsize, rawptr, rawsize))
def va2off(va):
    for name, va_, vsize, rawptr, rawsize in secs:
        if va_ <= va < va_+max(vsize,rawsize): return rawptr + (va-va_)
md = Cs(CS_ARCH_X86, CS_MODE_64)
def func_end(off, limit=0x4000):
    # stop at 16+ consecutive int3
    run = 0
    for i in range(limit):
        if d[off+i] == 0xcc:
            run += 1
            if run >= 12: return i - run + 1
        else:
            run = 0
    return limit
results = []
for idx, addr in enumerate(slots):
    rva = addr - base; off = va2off(rva)
    if off is None: continue
    size = func_end(off)
    code = d[off:off+size]
    hits = []
    for insn in md.disasm(code, rva):
        op = insn.op_str
        if insn.mnemonic in ("call","jmp") and "0xd8]" in op:
            hits.append("%s %s @+0x%x" % (insn.mnemonic, op, insn.address-rva))
    if hits:
        results.append((idx, rva, size, hits))
for idx, rva, size, hits in results:
    print("idx %2d rva=0x%08x size=%d :: %s" % (idx, rva, size, " | ".join(hits[:2])))
print("total:", len(results))
