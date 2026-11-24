
import socket, json
def rpc(c, t=240):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("stat:", rpc("stat"))
r = rpc("funcs chat")
print("funcs chat ->", r.get("matched"), r.get("functions", [])[:12])
r = rpc("funcs Broadcast")
print("funcs Broadcast ->", r.get("matched"), r.get("functions", [])[:12])
cls = rpc("classes 400")
names = [c["name"] for c in cls.get("classes", [])]
chat_cls = [n for n in names if "Chat" in n or "SCUM" in n]
print("chat/scum classes:", chat_cls[:20])
