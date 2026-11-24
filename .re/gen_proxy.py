
import struct, os
dll = r"C:\Windows\System32\dwmapi.dll"
d = open(dll,'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]; coff = e + 4
nsec = struct.unpack_from('<H', d, coff+2)[0]; optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff + 20; pe32p = (struct.unpack_from('<H', d, opt)[0] == 0x20b)
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
names = sorted(set(names))

base = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin"

# 1) asm thunks
asm = ["; auto-generated dwmapi forwarders", ".data"]
for n in names:
    asm.append(f"PUBLIC p_{n}")
    asm.append(f"p_{n} QWORD 0")
asm.append(".code")
for n in names:
    asm.append(f"PUBLIC {n}")
    asm.append(f"{n} PROC")
    asm.append(f"    jmp qword ptr [p_{n}]")
    asm.append(f"{n} ENDP")
asm.append("END")
open(os.path.join(base, "dwmapi_thunks.asm"), "w").write("\n".join(asm) + "\n")

# 2) def with plain export names
defl = ["LIBRARY dwmapi", "EXPORTS"] + [f"    {n}" for n in names]
open(os.path.join(base, "dwmapi_proxy.def"), "w").write("\n".join(defl) + "\n")

# 3) C++ bridge
bridge = ['// auto-generated: forwarder storage + resolver', '#include <windows.h>', '#include <string.h>', '', 'extern "C" {']
for n in names:
    bridge.append(f"extern void* p_{n};")
bridge.append("}")
bridge.append("")
bridge.append("static const char* kExportNames[] = {")
for n in names:
    bridge.append(f'    "{n}",')
bridge.append("};")
bridge.append("static void** kSlots[] = {")
for n in names:
    bridge.append(f"    (void**)&p_{n},")
bridge.append("};")
bridge.append("")
bridge.append("void InitDwmapiForwarders(HMODULE self) {")
bridge.append("    char sys[MAX_PATH] = {0};")
bridge.append("    GetSystemDirectoryA(sys, MAX_PATH);")
bridge.append("    strcat_s(sys, MAX_PATH, \"\\\\dwmapi.dll\");")
bridge.append("    HMODULE real = LoadLibraryA(sys);")
bridge.append("    if (!real) return;")
bridge.append("    for (size_t i = 0; i < sizeof(kExportNames)/sizeof(kExportNames[0]); ++i) {")
bridge.append("        *kSlots[i] = (void*)GetProcAddress(real, kExportNames[i]);")
bridge.append("    }")
bridge.append("}")
open(os.path.join(base, "dwmapi_bridge.cpp"), "w").write("\n".join(bridge) + "\n")
print("generated", len(names), "forwarders")
