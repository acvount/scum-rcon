
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for ctx in ["KismetStringLibrary", "VoiceChatComponent", "KismetSystemLibrary"]:
    print(ctx, "->", json.dumps(rpc("cstest %s ToUpper" % ctx), ensure_ascii=False))
