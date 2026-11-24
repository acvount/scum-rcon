
import socket, json, struct
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("dumpobj LoadAssetClass 0x120")
print("count:", r.get("count"))
for it in r.get("items", [])[:2]:
    h = bytes.fromhex(it["hex"])
    print("obj", it["i"], it["class"], "len", len(h))
    for off in range(0, len(h), 16):
        chunk = h[off:off+16]
        q = struct.unpack_from("<Q", chunk, 0)[0] if len(chunk)>=8 else 0
        print("  0x%03x  %s  q0=0x%x" % (off, chunk.hex(' '), q))
