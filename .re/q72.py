
import socket, json
def rpc(c, t=120):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("callfunc KismetStringLibrary ToUpper abc")
h = bytes.fromhex(r["hex"])
data = int.from_bytes(h[16:24], "little")
n = int.from_bytes(h[24:28], "little")
print("ret FString: data=0x%x num=%d" % (data, n))
val = rpc("raw %x 8" % data)
print("raw:", val["hex"], "->", bytes.fromhex(val["hex"]).decode("utf-16-le","replace"))
