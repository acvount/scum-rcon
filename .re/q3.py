
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("classes 3000")
cs = r.get("classes", [])
print("total_classes:", r.get("total_classes"), "returned:", len(cs))
names = [c["name"] for c in cs]
print("SCUM-related:", [n for n in names if "SCUM" in n][:20])
print("Chat:", [n for n in names if "Chat" in n][:20])
print("Player/Controller:", [n for n in names if "PlayerController" in n or "Character" in n][:10])
print("GameMode:", [n for n in names if "GameMode" in n][:10])
