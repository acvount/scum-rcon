
import struct, os, sys

path = r"D:\SCUM_Server\server\SCUM\Content\Paks\pakchunk0-WindowsServer.pak"
size = os.path.getsize(path)
print("pak size:", size)
MAGIC = 0x5A6F12E1

with open(path, 'rb') as f:
    # scan last 0x200 bytes for footer magic
    f.seek(max(0, size - 0x200))
    tail = f.read()
    pos = tail.rfind(struct.pack('<I', MAGIC))
    if pos < 0:
        print("footer magic not found in tail"); sys.exit(0)
    abs_pos = size - len(tail) + pos
    print("magic at 0x%x" % abs_pos)
    # footer layout (v11): EncryptionKeyGuid(16) bEncryptedIndex(1) Magic(4) Version(4) IndexOffset(8) IndexSize(8) IndexHash(20)
    f.seek(abs_pos - 16 - 1)
    hdr = f.read(1 + 4 + 4 + 8 + 8 + 20)
    enc = hdr[0]
    magic = struct.unpack_from('<I', hdr, 1)[0]
    ver = struct.unpack_from('<i', hdr, 5)[0]
    idx_off = struct.unpack_from('<q', hdr, 9)[0]
    idx_size = struct.unpack_from('<q', hdr, 17)[0]
    print("encryptedIndex=%d version=%d indexOffset=0x%x indexSize=%d" % (enc, ver, idx_off, idx_size))
    if idx_off <= 0 or idx_size <= 0 or idx_off > size:
        print("unexpected index location"); sys.exit(0)
    f.seek(idx_off)
    idx = f.read(min(idx_size, 3 * 1024 * 1024))
    print("index bytes read:", len(idx))
    hits = 0
    for needle in [b"BP_ConZPlayerController", b"ConZPlayerController"]:
        c = idx.count(needle)
        print(needle.decode(), "->", c)
        hits += c
    if hits == 0:
        # sample some strings to prove index parsed
        import re
        names = re.findall(rb'[ -~]{8,}', idx[:400000])
        print("sample entries:", [n.decode() for n in names[:6]])
