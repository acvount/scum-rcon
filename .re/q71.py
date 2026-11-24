
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("fname 14454167:", json.dumps(rpc("fname 14454167"), ensure_ascii=False))
print("fname 12612401:", json.dumps(rpc("fname 12612401"), ensure_ascii=False))
# try loading with the plain object path (no _C) via loadbp on a simpler asset
r = rpc("loadbp /Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController")
print("loadbp noC:", json.dumps(r, ensure_ascii=False))
