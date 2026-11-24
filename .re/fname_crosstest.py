import json, socket, struct
def send(cmd, timeout=90):
    with socket.create_connection(("127.0.0.1", 17880), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())
def fname(i):
    r = send(f"fname {i}")
    return r.get("ok"), r.get("name", "")

# 收集一堆已知名字的 id 并反查
seen = {}
for needle in ("BP_ConZGameMode", "/Game/ConZ_Files/Blueprints/GameModes", "BlueprintGeneratedClass", "BP_ConZPlayerController", "/Game/ConZ_Files/Blueprints/PlayerControllers", "ReturnValue", "AssetClass"):
    r = send(f'nameidx "{needle}" 30')
    for h in r.get("hits", []):
        seen.setdefault(h["id"], h["name"])
rows = []
for nid, nm in sorted(seen.items()):
    blk = nid >> 16
    ok, got = fname(nid)
    match = "MATCH" if (ok and got == nm) else ("DECODES-DIFF" if ok else "FAIL")
    rows.append((blk, nid, nm, match, got[:40] if got else ""))
rows.sort()
for blk, nid, nm, match, got in rows:
    print(f"blk {blk:>3} id {nid:>9} {match:>12} '{nm}' -> '{got}'")
