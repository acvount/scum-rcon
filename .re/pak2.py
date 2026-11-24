
import struct, os, re, sys
path = r"D:\SCUM_Server\server\SCUM\Content\Paks\pakchunk0-WindowsServer.pak"
size = os.path.getsize(path)
MAGIC = 0x5A6F12E1
with open(path, 'rb') as f:
    for tail_len in (0x2C, 0x40, 0x80, 0x100):
        f.seek(size - tail_len)
        t = f.read(tail_len)
        pos = t.find(struct.pack('<I', MAGIC))
        if pos < 0: continue
        # footer: [16 guid][1 enc][4 magic][4 ver][8 off][8 size][20 hash]
        start = size - tail_len + pos - 17
        f.seek(start)
        hdr = f.read(44)
        enc = hdr[0]
        ver = struct.unpack_from('<i', hdr, 5)[0]
        idx_off = struct.unpack_from('<q', hdr, 9)[0]
        idx_size = struct.unpack_from('<q', hdr, 17)[0]
        print("tail_len=%d enc=%d ver=%d off=0x%x size=%d (file=%d)" % (tail_len, enc, ver, idx_off, idx_size, size))
        if 0 < idx_off < size and 0 < idx_size < size:
            f.seek(idx_off)
            data = f.read(min(idx_size, 64*1024*1024))
            print("index read:", len(data))
            for needle in [b"BP_ConZPlayerController", b"ConZPlayerController", b"PlayerControllers"]:
                print("  ", needle.decode(), "->", data.count(needle))
            names = re.findall(rb'/Game/[ -~]{6,120}', data[:2000000])
            print("  sample /Game paths:", [n.decode(errors='replace') for n in names[:5]])
            break
