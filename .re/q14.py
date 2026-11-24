
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
addr = 0x1aae2f79400
r = rpc("raw %x 96" % addr)
h = bytes.fromhex(r["hex"])
print("prop node @%x" % addr)
for off in range(0, len(h), 16):
    ch = h[off:off+16]
    q = struct.unpack_from("<Q", ch, 0)[0] if len(ch)>=8 else 0
    print("  0x%02x  %s  q=0x%x" % (off, ch.hex(' '), q))
