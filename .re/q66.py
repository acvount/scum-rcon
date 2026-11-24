
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for pid in [12010429]:
    print(pid, "->", json.dumps(rpc("fname %d" % pid), ensure_ascii=False))
r = rpc("nameidx BP_ConZPlayerController 20")
print("nameidx hits:")
for h in r.get("hits", [])[:10]:
    print("   ", h["id"], h["name"])
