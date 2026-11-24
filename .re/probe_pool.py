
import socket, json, struct

def rpc(cmd):
    s = socket.create_connection(("127.0.0.1", 17880), timeout=30)
    s.sendall((cmd+"\n").encode())
    buf=b""
    while not buf.endswith(b"\n"):
        c=s.recv(1<<20)
        if not c: break
        buf+=c
    return json.loads(buf.decode("utf-8","replace"))

pool = 0x7ff77225b4d8
for addr, ln in [(pool, 32), (pool+0x10, 32)]:
    r = rpc("raw %x %d" % (addr, ln))
    print(hex(addr), r.get("hex"))
    if r.get("hex"):
        h = bytes.fromhex(r["hex"])
        vals = struct.unpack_from("<QQQQ", h, 0) if len(h)>=32 else ()
        print("   qwords:", [hex(v) for v in vals[:4]])
