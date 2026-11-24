import struct
import scum_admin as sa

h = sa.H(); st = h.init()
fn = None
for f in h.send("dumpfuncsraw").get("functions", []):
    if h.dn(f["nameId"]) == "BroadcastChatLine":
        fn = int(f["addr"]); break
print("BroadcastChatLine:", hex(fn))
b = h.raw(fn, 0xE0)
psz = struct.unpack("<H", b[0xB6:0xB8])[0]
print("parmsSize:", psz)
chain = struct.unpack("<Q", b[0x50:0x58])[0]
cur = chain
props = []
for k in range(8):
    if not cur: break
    pb = h.raw(cur, 0x60)
    nid = struct.unpack("<I", pb[0x28:0x2C])[0]
    esz = struct.unpack("<I", pb[0x3C:0x40])[0]
    off = struct.unpack("<I", pb[0x4C:0x50])[0]
    cls = struct.unpack("<Q", pb[0x10:0x18])[0]
    cn = h.dn(h.rdu32(cls + 0x18)) if cls else ""
    print(f"  prop {h.dn(nid)!r} size={esz} off={off} propClass={cn}")
    props.append((cur, h.dn(nid), esz, off, cn))
    cur = struct.unpack("<Q", pb[0x20:0x28])[0]

# 找 ChatType 属性，读它的 Enum 指针
for paddr, pname, psz2, poff, pcls in props:
    if pname != "ChatType":
        continue
    pb = h.raw(paddr, 0x80)
    print("\nChatType prop bytes:")
    for o2 in range(0, 0x80, 8):
        v = struct.unpack("<Q", pb[o2:o2+8])[0]
        print(f"  +{o2:#04x}: {v:#x}")
    # 尝试每个疑似 UEnum 指针
    for o2 in range(0x08, 0x80, 8):
        v = struct.unpack("<Q", pb[o2:o2+8])[0]
        if not (0x10000 < v < 0x7FFFFFFFFFFF):
            continue
        try:
            cl = h.rd64(v + 0x10)
            cn = h.dn(h.rdu32(cl + 0x18)) if cl else ""
        except Exception:
            continue
        if "Enum" in cn:
            print(f"\n== UEnum @+{o2:#x} -> {v:#x} class={cn} ==")
            # UEnum: TArray<TPair<FName,int64>> Names 通常在 0x40
            for noff in (0x40, 0x38, 0x48, 0x50):
                try:
                    data = h.raw(v + noff, 16)
                    ptr, num, mx = struct.unpack("<Qii", data)
                    if not (0x10000 < ptr < 0x7FFFFFFFFFFF) or not (0 < num < 200):
                        continue
                    print(f"   Names @+{noff:#x}: ptr={ptr:#x} num={num} max={mx}")
                    for i2 in range(min(num, 40)):
                        ent = h.raw(ptr + i2 * 16, 16)
                        fid = struct.unpack("<I", ent[0:4])[0]
                        val = struct.unpack("<q", ent[8:16])[0]
                        print(f"      [{i2}] {h.dn(fid)!r} = {val}")
                    break
                except Exception:
                    continue
