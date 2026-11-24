
import struct, sys

p = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
d = open(p,'rb').read()

e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
assert d[e_lfanew:e_lfanew+4] == b'PE\0\0'
coff = e_lfanew + 4
nsec = struct.unpack_from('<H', d, coff+2)[0]
opt_size = struct.unpack_from('<H', d, coff+16)[0]
opt = coff + 20
magic = struct.unpack_from('<H', d, opt)[0]
pe32p = magic == 0x20b
dd_off = opt + (112 if pe32p else 96)
imp_rva, imp_size = struct.unpack_from('<II', d, dd_off + 8)
sec_off = opt + opt_size
secs = []
for i in range(nsec):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((name, va, vsize, rawptr, rawsize))
print("sections:", [(s[0], hex(s[2])) for s in secs])

def rva2off(rva):
    for name, va, vsize, rawptr, rawsize in secs:
        if va <= rva < va + max(vsize, rawsize):
            return rawptr + (rva - va)
    return None

off = rva2off(imp_rva)
dlls = []
while True:
    desc = d[off:off+20]
    name_rva = struct.unpack_from('<I', desc, 12)[0]
    if name_rva == 0: break
    no = rva2off(name_rva)
    nm = d[no:d.index(b'\0', no)].decode('latin1')
    dlls.append(nm)
    off += 20
print("imports:", dlls)

KNOWN = set(x.lower() for x in [
 "kernel32.dll","user32.dll","gdi32.dll","advapi32.dll","shell32.dll","ole32.dll",
 "oleaut32.dll","comdlg32.dll","comctl32.dll","ws2_32.dll","ntdll.dll","rpcrt4.dll",
 "shlwapi.dll","imm32.dll","wininet.dll","crypt32.dll","msvcrt.dll","normaliz.dll",
 "sechost.dll","cfgmgr32.dll","bcrypt.dll","wintrust.dll","psapi.dll","iphlpapi.dll",
 "uxtheme.dll","dnsapi.dll","dhcpcsvc.dll","winhttp.dll","urlmon.dll","setupapi.dll",
 "version.dll","d3d11.dll","dxgi.dll","dwmapi.dll","winmm.dll","dbghelp.dll",
 "userenv.dll","wtsapi32.dll","ncrypt.dll","d3dcompiler_47.dll","xinput1_3.dll",
 "hid.dll","powrprof.dll","bthprops.cpl","avrt.dll","mfplat.dll","dsound.dll",
 "opengl32.dll","wldap32.dll","mswsock.dll","msimg32.dll","d3d9.dll","dxva2.dll",
 "evr.dll","mf.dll","mfreadwrite.dll","oleacc.dll","propsys.dll","wintypes.dll",
 "twinapi.appcore.dll","dcomp.dll","d2d1.dll","dwrite.dll","d3d12.dll",
])
cands = [x for x in dlls if x.lower() not in KNOWN and not x.lower().startswith(("api-ms","ext-ms"))]
print("hijack candidates (not in KnownDLLs):", cands)
