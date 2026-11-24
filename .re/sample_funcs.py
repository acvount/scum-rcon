
import socket, json, sys
def rpc(c, t=240):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))

r = rpc("funcs ")
print("matched:", r.get("matched"))
print("sample:", r.get("functions", [])[:20])
for kw in ["chat", "message", "item", "spawn"]:
    rr = rpc("funcs " + kw)
    print(kw, "->", rr.get("matched"), rr.get("functions", [])[:10])
