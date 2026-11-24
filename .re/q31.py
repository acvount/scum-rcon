
import socket, json, struct
def rpc(c, t=240):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for addr in [0x25c25c43330, 0x25c18913100, 0x25c1eb90880, 0x25c258efc50]:
    r = rpc("raw %x 40" % addr)
    h = bytes.fromhex(r["hex"])
    vt, fl, idx = struct.unpack_from("<Qii", h, 0)
    cls, = struct.unpack_from("<Q", h, 0x10)
    nidx, nnum = struct.unpack_from("<iI", h, 0x18)
    outer, = struct.unpack_from("<Q", h, 0x20)
    nm = rpc("fname %d" % nidx)
    cn = None
    if cls:
        rc = rpc("raw %x 32" % cls)
        hc = bytes.fromhex(rc["hex"])
        cidx, = struct.unpack_from("<i", hc, 0x18)
        cn = rpc("fname %d" % cidx)
    print("obj@0x%x name=%s class=%s(vt=0x%x idx=%d)" % (addr, nm.get("name"), cn.get("name") if cn else "?", vt, idx))
