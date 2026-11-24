
import struct
base = 0x7ff76b010000
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

# 现在进程的 module base
cur_base = 0x7ff76b010000
cands = {64: 140700638386352, 65: 140700676831872}
pats = {
  "mov eax,[rdx+0xB0]": bytes.fromhex("8b82b0000000"),
  "mov ecx,[rdx+0xB0]": bytes.fromhex("8b8ab0000000"),
  "test byte [rdx+0xB0]": bytes.fromhex("f682b0000000"),
  "cmp byte [rdx+0xB0]": bytes.fromhex("80bab0000000"),
}
for idx, a in cands.items():
    rva = a - cur_base
    off = va2off(rva)
    body = d[off:off+0x300]
    print("== idx", idx, "rva=0x%x" % rva)
    print("   head:", body[:24].hex(' '))
    for name, p in pats.items():
        pos = body.find(p)
        if pos >= 0: print("   FOUND %s at +0x%x" % (name, pos))
    # look for calls and memory ops on rdx
    print("   rdx refs:", [hex(i) for i in range(len(body)-2) if body[i:i+2] == b'\x8b\x82'][:8])
