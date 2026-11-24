# 新 exe 上 exec 核心验证：ToUpper（已知单参数）→ Chat_Server_ProcessAdminCommand
import json, socket, struct, sys
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
print("module:", st["module"], "objects:", st["objects"])
r2 = send("dumpfuncsraw")
addrs = {}
for f in r2.get("functions", []):
    nm = decode_name(pool, f["nameId"])
    if nm in ("ToUpper", "Chat_Server_ProcessAdminCommand", "BroadcastChatLine", "Test_ProcessAdminCommand"):
        addrs.setdefault(nm, []).append(int(f["addr"]))
print("targets:", {k: [hex(x) for x in v] for k, v in addrs.items()})

# 1) ToUpper：KismetStringLibrary(静态, ctx=KSL CDO)，参数 WorldContextObject? 实际 ToUpper 无 ctx 参数
if "ToUpper" in addrs:
    a = addrs["ToUpper"][0]
    d = send(f"descaddr {a:x}")
    print("ToUpper desc:", json.dumps(d, ensure_ascii=False))
    # 单参数 s@0（无 return 偏移时 retOff=0xffff）
    c = send(f'gtcall 0x{a:x} CDO:KismetStringLibrary 0:s:"abc"')
    print("ToUpper:", json.dumps(c, ensure_ascii=False))

# 2) Chat_Server_ProcessAdminCommand: 1 个 FString @0
if "Chat_Server_ProcessAdminCommand" in addrs:
    a = addrs["Chat_Server_ProcessAdminCommand"][0]
    c = send(f'gtcall 0x{a:x} 0:s:"Help"')
    print("Chat_Server_ProcessAdminCommand:", json.dumps(c, ensure_ascii=False))

# 3) BroadcastChatLine
if "BroadcastChatLine" in addrs:
    a = addrs["BroadcastChatLine"][0]
    w = send("findinst BP_ConZGameMode_C 10")
    ctx = int(w["items"][0]["addr"]) if w.get("items") else 0
    print("ctx:", hex(ctx))
    c = send(f'gtcall 0x{a:x} 0:o:0x{ctx:x} 8:s:"probe" 24:i:0')
    print("BroadcastChatLine:", json.dumps(c, ensure_ascii=False))
S.close()
