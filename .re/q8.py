
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for cls in ["BP_ConZPlayerController", "PlayerController"]:
    r = rpc("members %s 400" % cls)
    mem = r.get("members", [])
    funcs = [m["name"] for m in mem if m["kind"]=="Function"]
    print("==", cls, "classes:", r.get("classes"), "members:", r.get("count"), "funcs:", len(funcs))
    print("   chat/broadcast:", [f for f in funcs if "Chat" in f or "Broadcast" in f or "Message" in f][:15])
    print("   sample:", funcs[:12])
