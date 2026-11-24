
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for idx in range(60, 76):
    r = rpc("strtest %d" % idx)
    print(idx, json.dumps(r, ensure_ascii=False))
    if r.get("result") == "ABC":
        print("  ==> ProcessEvent index =", idx); break
