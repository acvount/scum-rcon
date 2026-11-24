
import struct, re
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

start = 0x60B8000
end   = 0x60BA400
o1 = va2off(start); o2 = va2off(end)
blob = d[o1:o2]
print("region size", len(blob))
# ASCII strings
strs = re.findall(rb'[ -~]{4,}', blob)
print("ascii strings:", len(strs))
for s in strs:
    t = s.decode('latin1')
    if any(k in t for k in ("Chat","Admin","Message","Broadcast","Server","Client","Player","Item","Notify")):
        print("   ", t[:80])
# UTF-16 check
u16 = "Chat_Server_BroadcastChatMessage".encode('utf-16-le')
print("utf16 variant present:", d.find(u16) >= 0)
