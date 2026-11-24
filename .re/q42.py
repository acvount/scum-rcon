
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for name in ["ToUpper", "LoadClassAsset_Blocking", "GetGameTimeInSeconds"]:
    r = rpc("dumpobj %s 0xE8" % name)
    if not r.get("items"):
        print(name, "not found"); continue
    it = r["items"][0]
    h = bytes.fromhex(it["hex"])
    flags = struct.unpack_from("<I", h, 0xB0)[0]
    nump = struct.unpack_from("<H", h, 0xB4)[0]
    psz  = struct.unpack_from("<H", h, 0xB6)[0]
    rvo  = struct.unpack_from("<H", h, 0xB8)[0]
    func = struct.unpack_from("<Q", h, 0xD0)[0]
    print("%-26s flags=0x%08X native=%s numParms=%d parmsSize=%d retOff=%s func=0x%x"
          % (name, flags, bool(flags & 0x400), nump, psz,
             ("0x%x" % rvo) if rvo != 0xFFFF else "none", func))
