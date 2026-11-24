import json, socket, struct, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scum-harness", "client"))
import scum_admin as sa

h = sa.H(); st = h.init()
pool = h.pool
r = h.send("findclass AdminCommand_Location 20")
items = r.get("items", [])
print("AdminCommand_Location objects:", r.get("count"))
clsaddr = None
for it in items:
    a = int(it["addr"])
    nm = h.dn(it["nameId"])
    print(f"  i={it['i']} addr={a:#x} name={nm!r} class={it.get('class')!r}")
    if nm == "AdminCommand_Location":
        clsaddr = a
if not clsaddr:
    raise SystemExit(1)
cdo = struct.unpack("<Q", h.raw(clsaddr + 0x118, 8))[0]
print("CDO:", hex(cdo))
buf = b""
for start in range(0, 0x1000, 0x200):
    try:
        buf += h.raw(cdo + start, 0x200)
    except Exception:
        break
print("cdo bytes:", len(buf))
def read_utf16(ptr, n):
    try:
        d = h.raw(ptr, n * 2)
        s = d.decode("utf-16-le")
        if all(32 <= ord(c) < 127 for c in s):
            return s
    except Exception:
        pass
    return None
seen = set()
for off in range(0, len(buf) - 8, 8):
    v = struct.unpack("<Q", buf[off:off + 8])[0]
    if not (0x10000 < v < 0x7FFFFFFFFFFF) or v in seen:
        continue
    seen.add(v)
    # 尝试按 FString 读取：Data 指针处是 UTF-16 文本
    for n in (3, 4, 5, 6, 8, 10, 12, 16, 20):
        s = read_utf16(v, n)
        if s and not s.startswith("\x00"):
            print(f"  +{off:#05x} -> FString-ish '{s}' (len {n})")
            break
        # 也尝试按 FName 解（比较 id）
    # 按 FName 尝试
    nid = struct.unpack("<I", buf[off:off+4])[0]
    if 0 < nid < 20000000:
        nm = h.dn(nid)
        if nm and len(nm) > 1 and all(32 <= ord(c) < 127 for c in nm):
            print(f"  +{off:#05x} -> FName '{nm}'")
