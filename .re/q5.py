
import socket, json, time
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("stat:", rpc("stat"))
r = rpc("nameidx None 5")
print("None ->", r.get("count"), r.get("hits"))
r = rpc("nameidx Byte 5")
print("Byte ->", r.get("count"), r.get("hits"))
r = rpc("nameidx 5")
print("empty-needle sample ->", r.get("count"), [h["name"] for h in r.get("hits",[])][:6])
