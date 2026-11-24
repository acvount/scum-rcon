
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("callfunc KismetStringLibrary ToUpper abc")
hexs = r.get("hex","")
abc = "ABC".encode('utf-16-le') in bytes.fromhex(hexs) if hexs else False
print(json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False))
print("ABC present:", abc)
if hexs: print("hex:", hexs[:96])
