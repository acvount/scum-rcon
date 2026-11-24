import json, socket
def send(cmd, timeout=60):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

def slots(cls, lo, hi):
    r = send(f"findvt {cls} {lo} {hi}")
    if not r.get("ok"):
        return {}
    return {s["i"]: s["a"] for s in r["slots"]}

ge = slots("GameEngine", 60, 96)
ksl = slots("KismetSystemLibrary", 60, 96)
print("slot  GameEngine            KismetSystemLibrary   same?")
for i in range(60, 96):
    g = ge.get(i); k = ksl.get(i)
    if g is None and k is None: continue
    same = "==" if g == k else "!="
    print(f"{i:>4}  {str(g):>22} {str(k):>22}  {same}")
