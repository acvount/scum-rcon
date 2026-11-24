
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("nameidx /Script/SCUM/ 500")
print("SCUM script names:", r.get("count"))
for h in r.get("hits", [])[:40]:
    print("  ", h["id"], h["name"])
r = rpc("nameidx Chat 500")
print("Chat names:", r.get("count"))
for h in r.get("hits", [])[:40]:
    print("  ", h["id"], h["name"])
