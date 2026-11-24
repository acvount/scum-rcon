
import socket, json
def rpc(c, t=120):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
best = []
for idx in range(50, 78):
    r = rpc("timetest %d" % idx)
    if r.get("ok"):
        d = r.get("d", 0); f = r.get("f", 0)
        if (0.1 < d < 1e7) or (0.1 < f < 1e7):
            print("HIT idx", idx, json.dumps(r))
            best.append(idx)
print("candidates:", best)
