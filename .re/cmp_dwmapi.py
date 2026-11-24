
import struct

def parse(path):
    d = open(path,'rb').read()
    e = struct.unpack_from('<I', d, 0x3C)[0]
    coff = e + 4
    nsec = struct.unpack_from('<H', d, coff+2)[0]
    optsz = struct.unpack_from('<H', d, coff+16)[0]
    opt = coff + 20
    pe32p = struct.unpack_from('<H', d, opt)[0] == 0x20b
    dd = opt + (112 if pe32p else 96)
    sec_off = opt + optsz
    secs = []
    for i in range(nsec):
        o = sec_off + i*40
        vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
        secs.append((va, vsize, rawptr, rawsize))
    def r2o(rva):
        for va, vsize, rawptr, rawsize in secs:
            if va <= rva < va + max(vsize, rawsize):
                return rawptr + (rva - va)
        return None
    return d, dd, r2o

def imports(path, want):
    d, dd, r2o = parse(path)
    imp_rva = struct.unpack_from('<I', d, dd+8)[0]
    off = r2o(imp_rva)
    out = []
    while True:
        desc = d[off:off+20]
        name_rva, ft = struct.unpack_from('<II', desc, 12)
        if name_rva == 0: break
        no = r2o(name_rva)
        nm = d[no:d.index(b'\0', no)].decode('latin1')
        if nm.lower() == want:
            thunk = struct.unpack_from('<I', desc, 0)[0]
            to = r2o(thunk)
            while True:
                v = struct.unpack_from('<Q', d, to)[0]
                if v == 0: break
                if v & (1<<63):
                    out.append(("ordinal", v & 0xFFFF))
                else:
                    fn = r2o(v & 0x7FFFFFFF)
                    out.append(("name", d[fn+2:d.index(b'\0', fn+2)].decode('ascii')))
                to += 8
        off += 20
    return out

def exports(path):
    d, dd, r2o = parse(path)
    er = struct.unpack_from('<I', d, dd)[0]
    eo = r2o(er)
    nnames = struct.unpack_from('<I', d, eo+24)[0]
    base = struct.unpack_from('<I', d, eo+16)[0]
    names_rva = struct.unpack_from('<I', d, eo+32)[0]
    no = r2o(names_rva)
    res = []
    for i in range(nnames):
        rva, = struct.unpack_from('<I', d, no + i*4)
        off = r2o(rva)
        res.append(d[off:d.index(b'\0', off)].decode('ascii'))
    return base, sorted(res)

exe = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
print("exe imports from dwmapi:", imports(exe, "dwmapi.dll"))
b1, sys_exp = exports(r"C:\Windows\System32\dwmapi.dll")
print("system exports:", len(sys_exp), "base", b1)
ours = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dwmapi.dll"
b2, our_exp = exports(ours)
print("our exports:", len(our_exp))
print("missing:", sorted(set(sys_exp) - set(our_exp)))
