
import socket, json
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for fn in ["LoadClassAsset_Blocking", "IsValid", "GetGameTimeInSeconds"]:
    r = rpc("calib " + fn)
    print("==", fn, "numParms=", r.get("numParms"), "parmsSize=", r.get("parmsSize"), "func=", r.get("func"))
    for c in r.get("cands", []):
        print("   ptrOff=0x%x -> %s next=%s" % (c["ptrOff"], c["ptr"], c["next"]))
        for n in c["names"]:
            print("        @0x%02x %s" % (n["off"], n["name"]))
