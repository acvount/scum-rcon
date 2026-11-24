
import socket, json, struct
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("strtest 65 KismetProceduralMeshLibrary")
print(json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False))
h = r.get("hex","")
if h:
    b = bytes.fromhex(h)
    for off in range(0, min(len(b),96), 16):
        print("  0x%02x %s" % (off, b[off:off+16].hex(' ')))
    # find UTF-16 "ABC"
    needle = "ABC".encode('utf-16-le')
    print("UTF16 ABC at:", [i for i in range(len(b)) if b[i:i+len(needle)]==needle])
