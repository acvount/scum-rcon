# 静态找 xrefs：call 0x1F31060（管理员集合 getter）的所有调用点
import struct

EXE = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
data = open(EXE, "rb").read()
e = struct.unpack_from("<I", data, 0x3C)[0]
ns = struct.unpack_from("<H", data, e + 6)[0]
osz = struct.unpack_from("<H", data, e + 20)[0]
secs = []
o = e + 24 + osz
for i in range(ns):
    p = o + i * 40
    nm = data[p:p+8].rstrip(b"\x00").decode("latin1")
    vs, va, rs, ra = struct.unpack_from("<IIII", data, p + 8)
    secs.append((nm, va, vs, ra, rs))

# .text
tname, tva, tvs, tra, trs = secs[0]
print("text:", tname, hex(tva), hex(tvs))
text = data[tra:tra+trs]

TARGETS = {
    0x1F31060: "admin set getter",
    0x1F8D8C0: "is-in-admin-check",
}

def scan(target):
    hits = []
    i = 0
    n = len(text)
    while i < n - 5:
        if text[i] == 0xE8:                      # call rel32
            rel = struct.unpack_from("<i", text, i + 1)[0]
            src = tva + i
            dst = src + 5 + rel
            if dst == target:
                hits.append(src)
        i += 1
    return hits

for t, name in TARGETS.items():
    hs = scan(t)
    print(f"\n{name} {t:#x}: {len(hs)} 处 call")
    for a in hs[:40]:
        print(f"   call @ {a:#x}")

# 也找 lea/mov 形式的地址引用
for t, name in TARGETS.items():
    pat = struct.pack("<II", 0, 0)
    hits = []
    i = 0
    while i < len(text) - 4:
        v = struct.unpack_from("<I", text, i)[0]
        if v == t:
            hits.append(tva + i)
        i += 4
    print(f"\n{name} {t:#x}: {len(hits)} 处 32 位立即数引用")
    for a in hits[:10]:
        print(f"   @ {a:#x}")
