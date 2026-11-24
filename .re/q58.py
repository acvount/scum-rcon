
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

def show(rva, n=0x40, label=""):
    off = va2off(rva)
    print("== %s 0x%x ==" % (label, rva))
    for insn in md.disasm(d[off:off+n], rva):
        print("  0x%08x  %-7s %s" % (insn.address, insn.mnemonic, insn.op_str))

show(0x2cb0890, 0x50, "candidate Invoke")

# does it read [reg+0xD8]?
off = va2off(0x2cb0890)
hit = None
for insn in md.disasm(d[off:off+0x2000], 0x2cb0890):
    if insn.mnemonic == "call" and "0xd8]" in insn.op_str:
        hit = "0x%x  %s %s" % (insn.address, insn.mnemonic, insn.op_str)
        break
print("  func call inside:", hit)

# find vtable slots that call 0x2cb0890 directly
print()
for idx, addr in enumerate(slots):
    rva = addr - base; o2 = va2off(rva)
    if o2 is None: continue
    for insn in md.disasm(d[o2:o2+0x800], rva):
        if insn.mnemonic == "call" and insn.op_str == "0x2cb0890":
            print("vtable idx %2d (rva 0x%x) calls Invoke at +0x%x" % (idx, rva, insn.address-rva))
            break
