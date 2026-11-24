
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("dumpfuncs")
fns = r.get("functions", [])
print("total functions:", r.get("count"), "received:", len(fns))
import collections
chat = [f for f in fns if "chat" in f["f"].lower()]
print("chat-ish:", len(chat))
for f in chat[:25]: print("   ", f["o"], ".", f["f"], sep="")
give = [f for f in fns if "give" in f["f"].lower() or "additem" in f["f"].lower()]
print("give-ish:", len(give))
for f in give[:15]: print("   ", f["o"], ".", f["f"], sep="")
json.dump(fns, open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\functions.json","w"), ensure_ascii=False)
print("saved")
