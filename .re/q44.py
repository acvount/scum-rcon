
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("dumpobj ToUpper 0xE8")
it = r["items"][0]
h = bytes.fromhex(it["hex"])
print("len", len(h))
for off in range(0xA0, min(len(h), 0xE8), 8):
    q = struct.unpack_from("<Q", h, off)[0]
    tag = ""
    if 0x7ff76b000000 <= q <= 0x7ff775000000: tag = "  <-- module pointer (.text/.rdata)"
    print("  0x%03x  %s  q=0x%x%s" % (off, h[off:off+8].hex(' '), q, tag))
