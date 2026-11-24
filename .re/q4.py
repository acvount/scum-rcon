
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for kw in ["BroadcastChatMessage","Chat_Server","ConZChat","GiveItem","SSChat"]:
    r = rpc("nameidx %s 6" % kw)
    print(kw, "count=", r.get("count"), [ (h["id"],h["name"]) for h in r.get("hits",[])[:3] ])
