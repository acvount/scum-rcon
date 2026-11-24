
import socket, json, time
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for kw in ["ConZPlayerController", "Chat_Server", "ConZGameMode"]:
    r = rpc("findobj %s 40" % kw)
    print("==", kw, "count:", r.get("count"))
    for it in r.get("items", [])[:12]:
        print("   ", it["i"], it["class"], "|", it["name"])
