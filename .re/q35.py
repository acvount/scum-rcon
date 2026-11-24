
import json, struct
r = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\vtable.json"))
base = int(r["base"])
slots = [int(s) for s in r["slots"]]
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

pats = {
 "call [rdx+D0]": bytes.fromhex("ff52d0"),
 "call [rax+D0]": bytes.fromhex("ff90d0000000"),
 "call [r9+D0]": bytes.fromhex("ff51d0"),
 "mov [?],D0": bytes.fromhex("d0000000"),
 "B0 ref": bytes.fromhex("b0000000"),
}
print("idx  rva        size   matches")
cands = []
for idx, addr in enumerate(slots):
    rva = addr - base
    off = va2off(rva)
    if off is None: continue
    body = d[off:off+0x800]
    found = []
    for nm, p in pats.items():
        pos = body.find(p)
        if pos >= 0: found.append("%s@+0x%x" % (nm, pos))
    # estimate size: first int3 run of >=8 bytes
    size = len(body)
    for i in range(0, len(body)-8):
        if body[i:i+8] == b'\xcc'*8:
            size = i; break
    if found or idx in (65,66,67,68):
        print("%3d 0x%08x %6d  %s" % (idx, rva, size, ", ".join(found)))
    if size > 500: cands.append((idx, rva, size, found))
print("\nlarge functions:", sorted(cands, key=lambda x:-x[2])[:8])
