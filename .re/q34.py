
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("vtdump")
print("base:", r.get("base"), "vt:", r.get("vt"), "slots:", len(r.get("slots",[])))
json.dump(r, open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\vtable.json","w"))
# analyze against exe
base = int(r["base"])
path = r"D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe"
d = open(path,'rb').read()
e = struct.unpack_from('<I', d, 0x3C)[0]; coff=e+4
nsec = struct.unpack_from('<H', d, coff+2)[0]; optsz = struct.unpack_from('<H', d, coff+16)[0]
opt = coff+20; sec_off = opt+optsz
secs=[]
for i in range(nsec):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o+8)
    secs.append((name, va, vsize, rawptr, rawsize))
def va2off(va):
    for name, va_, vsize, rawptr, rawsize in secs:
        if va_ <= va < va_+max(vsize,rawsize): return rawptr + (va-va_)
pats = [bytes.fromhex(x) for x in ("8b82b0000000","8b92b0000000","f682b0000000","80bab0000000","448b82b0000000","448b8ab0000000")]
for idx, s in enumerate(r.get("slots", [])):
    addr = int(s)
    rva = addr - base
    off = va2off(rva)
    if off is None or off+0x100 > len(d): continue
    body = d[off:off+0x140]
    found = [p.hex() for p in pats if p in body]
    head = body[:12].hex(' ')
    if found:
        print("idx %d rva=0x%x  head=%s  MATCH=%s" % (idx, rva, head, found))
