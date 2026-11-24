
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("CDOs:", json.dumps(rpc("findobj Default__Kismet 6"), ensure_ascii=False)[:400])
for lib in ["KismetProceduralMeshLibrary", "KismetStringLibrary"]:
    for idx in [65]:
        r = rpc("strtest %d %s" % (idx, lib))
        print(lib, idx, json.dumps(r, ensure_ascii=False))
