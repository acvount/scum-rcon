
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("find CDO:", json.dumps(rpc("findobj Default__KismetStringLibrary 3"), ensure_ascii=False)[:300])
for args in ["65 KismetStringLibrary ToUpper", "64 KismetStringLibrary ToUpper", "65 KismetSystemLibrary IsValid", "66 KismetSystemLibrary IsValid"]:
    print(args, "->", json.dumps(rpc("petest " + args), ensure_ascii=False))
