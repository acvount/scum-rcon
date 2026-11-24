
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("CDO scan:", rpc("findobj Default__KismetStringLibrary 3")[:300])
for args in ["65 KismetStringLibrary ToUpper", "64 KismetStringLibrary ToUpper", "65 KismetSystemLibrary IsValid"]:
    print(args, "->", rpc("petest " + args))
