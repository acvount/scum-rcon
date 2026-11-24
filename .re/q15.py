
import socket, json, struct
def rpc(c, t=300):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("dumpobj LoadClassAsset_Blocking 0x120")
it = r["items"][0]
h = bytes.fromhex(it["hex"])
print("obj", it["i"], it["class"])
parmsSize = struct.unpack_from("<H", h, 0xB6)[0]
numParms  = struct.unpack_from("<H", h, 0xB4)[0]
funcp     = struct.unpack_from("<Q", h, 0xD0)[0]
print("NumParms=%d ParmsSize=%d Func=0x%x" % (numParms, parmsSize, funcp))
# candidate child-properties pointers in 0x40..0x80
cands = {}
for off in range(0x38, 0x88, 8):
    v = struct.unpack_from("<Q", h, off)[0]
    if 0x10000 < v < 0x7fffffffffff:
        cands[off] = v
print("pointer candidates:", {hex(k):hex(v) for k,v in cands.items()})
for off, v in cands.items():
    rr = rpc("raw %x 64" % v)
    node = bytes.fromhex(rr["hex"])
    # try fname decode at each 4-byte aligned offset in first 0x30
    print("-- cand 0x%02x -> 0x%x" % (off, v))
    for no in range(0, 0x30, 4):
        cand_id = struct.unpack_from("<i", node, no)[0]
        if cand_id <= 0 or cand_id > 50000000: continue
        fr = rpc("fname %d" % cand_id)
        if fr.get("ok") and fr.get("name"):
            print("     @0x%02x id=%d name=%s" % (no, cand_id, fr["name"]))
