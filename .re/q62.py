
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
def flags_of(name):
    r = rpc("dumpobj %s 0x20" % name)
    for it in r.get("items", []):
        h = bytes.fromhex(it["hex"])
        fl = struct.unpack_from("<I", h, 8)[0]
        idx = struct.unpack_from("<i", h, 0xC)[0]
        print("%-34s class=%-24s flags=0x%08X internal=%d bit29=%d"
              % (name, it["class"], fl, idx, (fl >> 29) & 1))
for n in ["VoiceChat", "ToUpper", "KismetStringLibrary", "BP_ConZGameMode_C"]:
    flags_of(n)
