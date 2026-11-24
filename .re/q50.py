
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
# need vtable index configurable: strtest uses a[1]
for idx in [77, 76, 75]:
    r = rpc("strtest %d KismetStringLibrary" % idx)
    hexs = r.get("hex","")
    abc = "ABC".encode('utf-16-le') in bytes.fromhex(hexs) if hexs else False
    print("strtest", idx, json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False), "ABC=", abc)
    if abc:
        print("   HEX:", hexs[:80])
