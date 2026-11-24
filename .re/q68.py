
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for nm in ["MakeSoftClassPath", "Conv_SoftClassPathToSoftClassRef", "LoadClassAsset_Blocking"]:
    r = rpc("dumpobj %s 0xE8" % nm)
    if not r.get("items"): 
        print(nm, "not found"); continue
    h = bytes.fromhex(r["items"][0]["hex"])
    flags = struct.unpack_from("<I", h, 0xB0)[0]
    nump  = struct.unpack_from("<H", h, 0xB4)[0]
    psz   = struct.unpack_from("<H", h, 0xB6)[0]
    roff  = struct.unpack_from("<H", h, 0xB8)[0]
    fnc   = struct.unpack_from("<Q", h, 0xD8)[0]
    print("%-32s numParms=%d parmsSize=%-3d retOff=0x%-3x native=%s"
          % (nm, nump, psz, roff, bool(flags & 0x400)))
