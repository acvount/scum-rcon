# 附加验证：服务器健康 + DumpChatState + ProcessAdminCommand
import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=180)
def send(cmd):
    S.sendall((cmd + "\n").encode()); buf = b""
    while not buf.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): raise RuntimeError(r)
    return bytes.fromhex(r["hex"])
def rd64(a): return struct.unpack("<Q", raw(a, 8))[0]
def decode_name(pool, nid):
    if nid <= 0: return ""
    block = nid >> 16; off = (nid & 0xFFFF) * 2
    if block > 1024: return f"?{nid}"
    try:
        blk = rd64(pool + 0x10 + block * 8)
        hdr = struct.unpack("<H", raw(blk + off, 2))[0]
    except Exception:
        return f"?{nid}"
    wide = hdr & 1; ln = (hdr >> 6) & 0x3FF
    if not blk or ln == 0 or ln > 512: return f"?{nid}"
    data = raw(blk + off + 2, ln * (2 if wide else 1))
    return "".join(chr(w & 0x7F) for w in struct.unpack(f"<{ln}H", data)) if wide else data.decode("latin1")

st = send("stat"); pool = int(st["names"], 16)
print("stat ok:", st.get("ok"), "objects:", st.get("objects"))
r2 = send("dumpfuncsraw")
targets = {}
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    if nm in ("DumpChatState", "Chat_Server_ProcessAdminCommand", "Test_ProcessAdminCommand"):
        targets[nm] = int(f["addr"])
print("targets:", {k: hex(v) for k, v in targets.items()})
# DumpChatState：0 参数试试
if "DumpChatState" in targets:
    c = send(f"gtcall 0x{targets['DumpChatState']:x} CDO:SCUMChatManager")
    print("DumpChatState:", json.dumps(c, ensure_ascii=False))
    c2 = send(f"gtcall 0x{targets['DumpChatState']:x}")
    print("DumpChatState(default ctx):", json.dumps(c2, ensure_ascii=False))
# ProcessAdminCommand Help
if "Test_ProcessAdminCommand" in targets:
    c3 = send(f"gtcall 0x{targets['Test_ProcessAdminCommand']:x} s:Help")
    print("Test_ProcessAdminCommand:", json.dumps(c3, ensure_ascii=False))
S.close()
