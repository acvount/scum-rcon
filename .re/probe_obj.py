
import socket, json, struct

def rpc(cmd):
    s = socket.create_connection(("127.0.0.1", 17880), timeout=30)
    s.sendall((cmd+"\n").encode()); buf=b""
    while not buf.endswith(b"\n"):
        c=s.recv(1<<20)
        if not c: break
        buf+=c
    return json.loads(buf.decode("utf-8","replace"))

def rd(addr, ln):
    r = rpc("raw %x %d" % (addr, ln))
    h = r.get("hex")
    if not h: 
        print("read fail", hex(addr), r); return None
    return bytes.fromhex(h)

GU = 0x7ff7726ccb90
b = rd(GU, 0x30)
print("GUObjectArray head:", b.hex() if b else None)
if b:
    objs, pre, maxel, numel, maxch, numch = struct.unpack_from("<QQiiii", b, 0x10)
    print("Objects=%x Pre=%x Max=%d Num=%d MaxChunks=%d NumChunks=%d" % (objs, pre, maxel, numel, maxch, numch))
    ch0 = struct.unpack("<Q", rd(objs, 8))[0]
    print("chunk0=%x" % ch0)
    item0 = struct.unpack("<Q", rd(ch0, 8))[0]
    print("item0.Object=%x" % item0)
    o = rd(item0, 0x30)
    print("object bytes:", o.hex())
    vt = struct.unpack_from("<Q", o, 0)[0]
    flags, idx = struct.unpack_from("<ii", o, 8)
    cls = struct.unpack_from("<Q", o, 0x10)[0]
    nm_idx, nm_num = struct.unpack_from("<iI", o, 0x18)
    outer = struct.unpack_from("<Q", o, 0x20)[0]
    print("vtable=%x flags=%x internal=%d class=%x name=(%d,%d) outer=%x" % (vt, flags, idx, cls, nm_idx, nm_num, outer))
