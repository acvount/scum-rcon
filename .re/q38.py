
import json, struct
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
# modrm for [reg+disp32]: 0x80|(reg<<3)|rm  where rm=0(rax),1(rcx),2(rdx),3(rbx),6(rsi),7(rdi)
regs = {0:'rax',1:'rcx',2:'rdx',3:'rbx',6:'rsi',7:'rdi'}
pats = {}
for rm, rn in regs.items():
    for op in (0x8b, 0xf6, 0x80, 0x3b, 0x85):
        modrm = 0x80 | (0 << 3) | rm
        pats["%s [%s+0xB0]" % (hex(op), rn)] = bytes([op, modrm]) + b'\xb0\x00\x00\x00'
for rm, rn in regs.items():
    pats["mov r,[%s+0xB0](64)" % rn] = bytes([0x44, 0x8b, 0x80 | rm]) + b'\xb0\x00\x00\x00'
print("patterns:", len(pats))
found_any = False
for idx, addr in enumerate(slots):
    rva = addr - base; off = va2off(rva)
    if off is None: continue
    body = d[off:off+0x600]
    hits = [nm for nm, p in pats.items() if p in body]
    if hits:
        found_any = True
        print("idx %2d rva=0x%08x %s" % (idx, rva, hits))
print("any:", found_any)
