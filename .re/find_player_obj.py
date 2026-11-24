import json, socket, struct
S = socket.create_connection(("127.0.0.1", 17880), timeout=240)
def send(cmd):
    S.sendall((cmd + "\n").encode()); b = b""
    while not b.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        b += c
    return json.loads(b.decode("utf-8", "replace").strip())
for q in ("Player", "Prisoner", "Controller", "Character"):
    r = send("findobj %s 400" % q)
    items = r.get("items", [])
    hits = []
    for it in items:
        nm = it.get("name") or ""
        cls = it.get("class") or ""
        # 实例名通常含数字后缀，或类名非空且不是 Class/Function/Package
        if any(k in nm for k in ("Controller", "Prisoner", "Character", "Pawn")) and cls not in ("Class", "Function", "Package", "ScriptStruct"):
            hits.append((it["i"], it["name"], it["class"]))
    print("== findobj %s: total=%s hits=%d" % (q, r.get("count"), len(hits)))
    for h in hits[:25]:
        print("   i=%s name=%r class=%r" % h)
S.close()
