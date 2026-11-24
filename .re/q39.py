
import json, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
r = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\vtable.json"))
base = int(r["base"]); slots = [int(s) for s in r["slots"]]
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
md.detail = True
results = []
for idx, addr in enumerate(slots):
    rva = addr - base; off = va2off(rva)
    if off is None: continue
    code = d[off:off+0x600]
    hits = []
    for insn in md.disasm(code, rva):
        op = insn.op_str
        if ("0xb0]" in op) or ("0xd0]" in op):
            hits.append("%s %s" % (insn.mnemonic, op))
        if len(hits) >= 4: break
    if hits:
        results.append((idx, rva, hits))
for idx, rva, hits in results:
    print("idx %2d rva=0x%08x :: %s" % (idx, rva, " | ".join(hits)))
print("\ntotal:", len(results))
