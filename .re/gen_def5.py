
import struct
d = open(r"C:\Windows\System32\dwmapi.dll",'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]; coff = e+4
nsec = struct.unpack_from('<H', d, coff+2)[0]; optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff+20; pe32p = struct.unpack_from('<H', d, opt)[0] == 0x20b
dd = opt + (112 if pe32p else 96); sec_off = opt + optsz
secs = []
for i in range(nsec):
    o = sec_off + i*40
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((va, vsize, rawptr, rawsize))
def r2o(rva):
    for va, vsize, rawptr, rawsize in secs:
        if va <= rva < va + max(vsize, rawsize): return rawptr + (rva - va)
eo = r2o(struct.unpack_from('<I', d, dd)[0])
base = struct.unpack_from('<I', d, eo+16)[0]
nnames = struct.unpack_from('<I', d, eo+24)[0]
names_rva = struct.unpack_from('<I', d, eo+32)[0]
ord_rva = struct.unpack_from('<I', d, eo+36)[0]
no, oo = r2o(names_rva), r2o(ord_rva)
pairs = []
for i in range(nnames):
    nr = struct.unpack_from('<I', d, no + i*4)[0]
    off = r2o(nr)
    nm = d[off:d.index(b'\0', off)].decode('ascii')
    fi = struct.unpack_from('<H', d, oo + i*2)[0]
    pairs.append((nm, base + fi))
pairs.sort()
print("count", len(pairs), pairs[:3])
lines = ["LIBRARY dwmapi", "EXPORTS"]
for nm, od in pairs:
    lines.append("    %s @%d" % (nm, od))
open(r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dwmapi_proxy.def","w").write("\n".join(lines)+"\n")
print("ok")
