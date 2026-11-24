
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return b.decode("utf-8","replace")
print("stat:", rpc("stat"))
print("calib IsValid:", rpc("calib IsValid")[:400])
print("findobj IsValid:", rpc("findobj IsValid 5")[:400])
print("fname 0:", rpc("fname 0")[:200])
