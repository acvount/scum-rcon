
import socket, json
def rpc(c, t=120):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for idx in [68, 67, 69]:
    r = rpc("strtest %d KismetStringLibrary" % idx)
    hexs = r.get("hex","")
    abc = False
    if hexs:
        abc = "ABC".encode('utf-16-le') in bytes.fromhex(hexs)
    print(idx, json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False), "ABC=", abc)
    if abc:
        print("   hex:", hexs[:64])
