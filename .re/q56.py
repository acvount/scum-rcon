
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
md.detail = False
def scan_callsite(target_rva, limit=0x1200):
    off = va2off(target_rva)
    if off is None: return None
    try:
        for insn in md.disasm(d[off:off+limit], target_rva):
            if insn.mnemonic == "call" and "0xd8]" in insn.op_str:
                return "%s @+0x%x" % (insn.op_str, insn.address - target_rva)
    except Exception:
        pass
    return None
seen = {}
for idx, addr in enumerate(slots):
    rva = addr - base; off = va2off(rva)
    if off is None: continue
    try:
        for insn in md.disasm(d[off:off+0x600], rva):
            if insn.mnemonic != "call": continue
            t = insn.op_str
            if not t.startswith("0x"): continue
            try: tgt = int(t, 16)
            except: continue
            if tgt in seen: continue
            hit = scan_callsite(tgt)
            if hit:
                seen[tgt] = (idx, hit)
    except Exception:
        pass
for tgt, (idx, hit) in seen.items():
    print("call target 0x%x from vtable idx %d :: %s" % (tgt, idx, hit))
print("found:", len(seen))
