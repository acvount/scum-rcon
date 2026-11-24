
import struct
dll = r"C:\Windows\System32\dwmapi.dll"
d = open(dll,'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]; coff = e + 4
nsec = struct.unpack_from('<H', d, coff+2)[0]; optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff + 20; magic = struct.unpack_from('<H', d, opt)[0]; pe32p = magic == 0x20b
dd = opt + (112 if pe32p else 96)
exp_rva = struct.unpack_from('<I', d, dd)[0]
sec_off = opt + optsz; secs = []
for i in range(nsec):
    o = sec_off + i*40
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((va, vsize, rawptr, rawsize))
def r2o(rva):
    for va, vsize, rawptr, rawsize in secs:
        if va <= rva < va + max(vsize, rawsize): return rawptr + (rva - va)
eo = r2o(exp_rva)
nnames = struct.unpack_from('<I', d, eo+24)[0]
names_rva = struct.unpack_from('<I', d, eo+32)[0]
no = r2o(names_rva)
names = []
for i in range(nnames):
    rva = struct.unpack_from('<I', d, no + i*4)[0]
    off = r2o(rva)
    names.append(d[off:d.index(b'\0', off)].decode('ascii'))
lines = ["LIBRARY dwmapi", "EXPORTS"]
for n in sorted(names):
    lines.append(f"    {n}=dwmapi_orig.{n}")
open(r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dwmapi_proxy.def","w").write("\n".join(lines)+"\n")
print("exports", len(names))
