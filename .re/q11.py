
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
try:
    print("stat:", rpc("stat"))
except Exception as e:
    print("no channel:", e); raise SystemExit
r = rpc("dumpfuncs")
fns = r.get("functions", [])
print("functions now:", r.get("count"))
chat = [f for f in fns if "chat" in f["f"].lower()]
print("chat functions:", len(chat))
for f in chat[:20]: print("   ", f["o"], ".", f["f"], sep="")
for kw in ["RawByteStream","NetSerializ","ConZNet","NetConnection"]:
    rr = rpc("nameidx %s 60" % kw)
    names = [h["name"] for h in rr.get("hits",[])]
    print(kw, "->", rr.get("count"), names[:12])
json.dump(fns, open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\functions2.json","w"), ensure_ascii=False)
