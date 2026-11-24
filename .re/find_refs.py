
import struct

path = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
d = open(path,'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]
coff = e + 4
nsec = struct.unpack_from('<H', d, coff+2)[0]
optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff + 20
pe32p = struct.unpack_from('<H', d, opt)[0] == 0x20b
dd = opt + (112 if pe32p else 96)
imgbase = struct.unpack_from('<Q', d, opt+24)[0]
sec_off = opt + optsz
secs = []
for i in range(nsec):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((name, va, vsize, rawptr, rawsize))

def off2va(off):
    for name, va, vsize, rawptr, rawsize in secs:
        if rawptr <= off < rawptr + rawsize:
            return va + (off - rawptr)
    return None
def va2off(va):
    for name, va_, vsize, rawptr, rawsize in secs:
        if va_ <= va < va_ + max(vsize, rawsize):
            return rawptr + (va - va_)
    return None

targets = [b"Chat_Server_BroadcastChatMessage\x00",
           b"Chat_Server_ProcessAdminCommand\x00",
           b"Chat_Client_SendMessageToChat\x00"]
found = {}
for t in targets:
    i = d.find(t)
    if i < 0:
        print("not found:", t[:32]); continue
    va = off2va(i)
    found[t] = va
    print("string %-45s off=0x%x va=0x%x" % (t[:40].decode('latin1'), i, va))

text = [s for s in secs if s[0] == ".text"][0]
_, tva, tvsize, trawptr, trawsize = text
ts = trawptr; te = trawptr + trawsize

for t, va in found.items():
    hits = []
    for p in range(ts, te - 7):
        b0 = d[p]
        if b0 != 0x48: continue
        b1 = d[p+1]
        if b1 not in (0x8D, 0x8B): continue
        modrm = d[p+2]
        if modrm not in (0x0D, 0x15, 0x05, 0x1D): continue
        disp = struct.unpack_from('<i', d, p+3)[0]
        insn_va = off2va(p)
        if insn_va is None: continue
        target_va = insn_va + 7 + disp
        if target_va == va:
            hits.append(insn_va)
    print("%-45s refs=%d %s" % (t[:40].decode('latin1'), len(hits), [hex(h) for h in hits[:8]]))
