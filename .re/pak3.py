
import struct, os, re
path = r"D:\SCUM_Server\server\SCUM\Content\Paks\pakchunk0-WindowsServer.pak"
size = os.path.getsize(path)
MAGIC = 0x5A6F12E1
with open(path, 'rb') as f:
    f.seek(size - 0x200)
    t = f.read(0x200)
    for pos in [i for i in range(len(t)-3) if t[i:i+4] == struct.pack('<I', MAGIC)]:
        start = size - 0x200 + pos - 17
        if start < 0: continue
        f.seek(start)
        hdr = f.read(64)
        enc = hdr[16]
        ver = struct.unpack_from('<i', hdr, 21)[0]
        off = struct.unpack_from('<q', hdr, 25)[0]
        isz = struct.unpack_from('<q', hdr, 33)[0]
        print("candidate magic@%d enc=%d ver=%d off=0x%x size=%d" % (size-0x200+pos, enc, ver, off, isz))
        if not (0 < off < size and 0 < isz < size): continue
        f.seek(off)
        data = f.read(min(isz, 96*1024*1024))
        print("index bytes:", len(data))
        for needle in [b"BP_ConZPlayerController", b"ConZPlayerController", b"PlayerControllers"]:
            print("  ", needle.decode(), "->", data.count(needle))
        names = re.findall(rb'/Game/[ -~]{8,120}', data[:3000000])
        print("  sample paths:", [n.decode(errors='replace')[:90] for n in names[:6]])
        break
