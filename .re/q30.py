
import socket, json, struct
def rpc(c, t=240):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("dumpobj KismetSystemLibrary 0x200")
print("count:", r.get("count"))
it = r["items"][0]
print("class:", it["class"])
h = bytes.fromhex(it["hex"])
for off in range(0, len(h), 16):
    q = struct.unpack_from("<Q", h, off)[0] if off+8 <= len(h) else 0
    print("  0x%03x %s  q=0x%x" % (off, h[off:off+16].hex(' '), q))
