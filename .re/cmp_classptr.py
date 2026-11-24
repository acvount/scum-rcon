import json, socket, struct
def send(cmd, timeout=60):
    with socket.create_connection(("127.0.0.1", 17880), timeout=60) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def rd64(a):
    r = send(f"raw {a:x} 8")
    return struct.unpack("<Q", bytes.fromhex(r["hex"]))[0]
st = send("stat"); gob = int(st["gobjects"], 16)
chunk0 = rd64(rd64(gob + 0x10))
def obj_addr(i): return rd64(chunk0 + i * 0x18)
r = send('findobj ConZGameMode 10')
for it in r["items"]:
    if "C" in it["name"] or "GameMode" == it["name"]:
        a = obj_addr(it["i"])
        print(f"i={it['i']} name={it['name']} class={it['class']} addr={a:#x}")
print("mode1 GameMode classPtr was: 0x23b37b66000")
print("mode1 PlayerCtrl classPtr was: 0x23b355a5000")
