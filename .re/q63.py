
import json, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
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
rva = 140700703742944 - 0x7ff76b010000
print("Func rva = 0x%x" % rva)
off = va2off(rva)
for insn in md.disasm(d[off:off+0xC0], rva):
    print("  0x%08x  %-7s %s" % (insn.address, insn.mnemonic, insn.op_str))
