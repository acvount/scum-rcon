
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for idx in range(64, 76):
    r = rpc("petest %d" % idx)
    print(idx, "ok=", r.get("ok"), "result=", r.get("result"), "ex=", r.get("ex"), "addr=", r.get("addr"))
    if r.get("ok") and r.get("result") == 1:
        print("  ==> ProcessEvent index likely", idx); break
