
import sys, re, struct
p = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
data = open(p,'rb').read()
print("size", len(data))
# UTF-16LE "++UE"
pat16 = "++UE".encode('utf-16-le')
idxs = [m.start() for m in re.finditer(re.escape(pat16), data)][:10]
print("utf16 ++UE hits:", len(idxs))
for i in idxs[:6]:
    chunk = data[i:i+80]
    try: s = chunk.decode('utf-16-le', 'ignore')
    except: s = ''
    print("  @%x" % i, repr(s[:40]))
# ASCII
for pat in [b"++UE", b"Release-5", b"++UE5"]:
    hits = [m.start() for m in re.finditer(re.escape(pat), data)][:5]
    print(pat, len(hits), [hex(h) for h in hits])
# 常见版本字符串
for pat in [b"5.4.", b"5.3.", b"5.2.", b"5.1.", b"5.0."]:
    hits = [m.start() for m in re.finditer(re.escape(pat), data)][:3]
    if hits:
        for h in hits[:2]:
            print(pat, hex(h), repr(data[h-24:h+24]))
