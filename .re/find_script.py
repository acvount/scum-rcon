# 找 UFunction::Script 偏移：扫描 0x58..0xAC 的 qword，raw 读候选，看字节码特征
import json, socket, struct
def send(cmd, timeout=60):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"): return None
    return bytes.fromhex(r["hex"])

r = send('dumpobj LoadClassAsset_Blocking 200')
hexs = r["items"][0]["hex"]
obj = bytes.fromhex(hexs)
print("=== UFunction qwords 0x40..0xAC ===")
for off in range(0x40, 0xB0, 8):
    v = struct.unpack("<Q", obj[off:off+8])[0]
    note = ""
    if 0x10000 < v < 0x7FFFFFFFFFFF:
        d = raw(v, 24)
        if d is not None:
            note = d.hex(" ")
            # 字节码特征：EX_LocalVariable(0x00)/EX_Return(0x04)/EX_EndOfScript(0x53) 打头或含 0x00 后跟指针
    print(f"+{off:02x}: {v:#018x}  {note}")
