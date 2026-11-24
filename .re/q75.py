
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for kw in ["GameInstance", "GameEngine"]:
    r = rpc("findobj %s 8" % kw)
    print("==", kw, r.get("count"))
    for it in r.get("items", [])[:8]:
        print("   %6d  %-28s %s" % (it["i"], it["class"], it["name"]))
