
import socket, json
def rpc(c, t=120):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
hits = []
for idx in range(58, 86):
    r = rpc("strtest %d KismetStringLibrary" % idx)
    hexs = r.get("hex","")
    abc = False
    if hexs:
        b = bytes.fromhex(hexs)
        abc = "ABC".encode('utf-16-le') in b
    if abc or r.get("ex", 0) != 0:
        print(idx, "ex=", r.get("ex"), "ABC=", abc)
        hits.append((idx, abc, r.get("ex", 0)))
print("candidates:", hits)
