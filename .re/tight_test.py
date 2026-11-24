# 紧时序：gtload 后立刻检查返回对象 + 对象表
import json, socket, struct, subprocess, sys

def send(cmd, timeout=90):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"):
        return None
    return bytes.fromhex(r["hex"])

path = "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C"
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 0
r = send(f'gtload "{path}" 86 14 {tid} GameEngine 1')
cp = int(r["classPtr"]) if r.get("classPtr") else 0
print("gtload:", json.dumps(r, ensure_ascii=False))
if cp:
    b = raw(cp, 0x40)
    if b:
        vt = struct.unpack("<Q", b[0:8])[0]
        flags = struct.unpack("<I", b[8:12])[0]
        idx = struct.unpack("<I", b[12:16])[0]
        cls = struct.unpack("<Q", b[0x10:0x18])[0]
        name = struct.unpack("<II", b[0x18:0x20])
        outer = struct.unpack("<Q", b[0x20:0x28])[0]
        print(f"obj @{cp:#x}: vt={vt:#x} flags={flags:#x} idx={idx} cls={cls:#x} name={name} outer={outer:#x}")
        nm = send(f"fname {name[0]}")
        print("name decode:", nm)
        if cls:
            cb = raw(cls, 0x30)
            if cb:
                cn = struct.unpack("<II", cb[0x18:0x20])
                print("class obj name id:", cn, "->", send(f"fname {cn[0]}"))
# 立刻查对象表
r2 = send("findobj BP_ConZPlayerController 10")
print("findobj:", json.dumps(r2, ensure_ascii=False))
r3 = send("funcs Chat_Server")
print("funcs Chat_Server:", json.dumps(r3, ensure_ascii=False))
