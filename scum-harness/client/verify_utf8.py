# -*- coding: utf-8 -*-
import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=240)
def send(cmd):
    S.sendall((cmd + "\n").encode("utf-8")); buf = b""
    while not buf.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send("raw %x %d" % (a, ln))
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def dn(pool, nid):
    if nid <= 0: return ""
    blk = rd64(pool + 0x10 + ((nid >> 16) * 8))
    if not blk: return ""
    off = (nid & 0xFFFF) * 2
    hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if ln == 0 or ln > 512: return "?%d" % nid
    d = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack("<%dH" % ln, d)) if wide else d.decode("latin1")

st = send("stat"); pool = int(st["names"], 16)
fn = None
for f in send("dumpfuncsraw").get("functions", []):
    if dn(pool, f["nameId"]) == "Concat_StrStr":
        fn = int(f["addr"]); break
A = "\u4f60\u597d"; B = "\uff01"
print("call:", json.dumps(send("gtcallpe %#x 0:s:%s 16:s:%s" % (fn, A, B)), ensure_ascii=True))
g = send("gtparms 0 128")
b = bytes.fromhex(g["hex"])
print("parms_size:", g.get("size"))
for name, off in (("A", 0), ("B", 16), ("Ret", 32)):
    ptr, num, mx = struct.unpack("<Qii", b[off:off+16])
    txt = ""
    if 0x1000 < ptr < 0x7FFFFFFFFFFF and 0 < num < 200:
        try:
            txt = raw(ptr, num * 2).decode("utf-16-le", "replace")
        except Exception as e:
            txt = "<read fail %s>" % e
    print("%s off=%d ptr=%#x num=%d text=%r codepoints=%s" % (name, off, ptr, num, txt, [hex(ord(c)) for c in txt]))
S.close()
