
import struct
path = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
d = open(path,'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]; coff = e+4
nsec = struct.unpack_from('<H', d, coff+2)[0]; optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff+20; pe32p = struct.unpack_from('<H', d, opt)[0]==0x20b
sec_off = opt + optsz
secs = []
for i in range(nsec):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((name, va, vsize, rawptr, rawsize))
def off2va(off):
    for name, va, vsize, rawptr, rawsize in secs:
        if rawptr <= off < rawptr+rawsize: return va + (off-rawptr)
def va2off(va):
    for name, va_, vsize, rawptr, rawsize in secs:
        if va_ <= va < va_+max(vsize,rawsize): return rawptr + (va-va_)
def rd_cstr(va, maxlen=96):
    o = va2off(va)
    if o is None: return None
    end = d.index(b'\0', o, o+maxlen) if b'\0' in d[o:o+maxlen] else None
    if end is None: return None
    try: return d[o:end].decode('latin1')
    except: return None

targets = {}
for t in [b"Chat_Server_BroadcastChatMessage\x00", b"Chat_Server_ProcessAdminCommand\x00", b"Chat_Client_SendMessageToChat\x00"]:
    i = d.find(t)
    if i >= 0: targets[t.rstrip(b"\0").decode()] = off2va(i)

text = [s for s in secs if s[0]==".text"][0]
_, tva, tvsize, trawptr, trawsize = text
ts, te = trawptr, trawptr+trawsize

def scan_refs(va):
    out = []
    for p in range(ts, te-7):
        b0 = d[p]
        if b0 not in (0x48,0x4C): continue
        if d[p+1] != 0x8D: continue
        m = d[p+2]
        # mod=00, rm=101  -> rip-relative
        if (m & 0xC7) != 0x05: continue
        insn_va = off2va(p)
        if insn_va is None: continue
        disp = struct.unpack_from('<i', d, p+3)[0]
        if insn_va + 7 + disp == va: out.append(insn_va)
    return out

for name, va in targets.items():
    refs = scan_refs(va)
    print("%-40s va=0x%x refs=%d %s" % (name, va, len(refs), [hex(r) for r in refs[:6]]))
    for r in refs[:3]:
        # near-strings context: scan +-0x300 for other string refs
        near = []
        base = r - 0x300
        for p in range(max(ts,base), min(te-7, r+0x300)):
            if d[p] not in (0x48,0x4C) or d[p+1] != 0x8D: continue
            m = d[p+2]
            if (m & 0xC7) != 0x05: continue
            iva = off2va(p)
            if iva is None: continue
            disp = struct.unpack_from('<i', d, p+3)[0]
            s = rd_cstr(iva+7+disp)
            if s and len(s) >= 4 and all(32 <= ord(c) < 127 for c in s):
                near.append((hex(iva), s))
        print("   near ref @%s:" % hex(r))
        for a,s in near[:14]: print("      ", a, s[:70])
