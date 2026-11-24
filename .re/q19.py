
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return b.decode("utf-8","replace")
print("petest 68:", rpc("petest 68")[:300])
print("findobj Default__Kismet:", rpc("findobj Default__Kismet 5")[:400])
print("findobj KismetSystemLibrary:", rpc("findobj KismetSystemLibrary 5")[:400])
