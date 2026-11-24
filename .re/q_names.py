
import socket, json
def rpc(c, t=120):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for kw in ["BroadcastChatMessage", "Chat_Server", "SSChatManager", "GiveItem"]:
    r = rpc("nameidx " + kw + " 8")
    print(kw, "count=", r.get("count"))
    for h in r.get("hits", [])[:4]:
        print("   ", h["id"], h["name"])
