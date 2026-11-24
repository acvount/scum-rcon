
import socket, json
def rpc(c, t=120):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("raw 22a30aa7810 8")
h = bytes.fromhex(r["hex"])
print("raw:", h.hex(' '))
print("as utf16:", h.decode('utf-16-le', 'replace'))
