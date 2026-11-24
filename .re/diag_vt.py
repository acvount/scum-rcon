import json, socket, struct, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scum-harness", "client"))
import scum_admin as sa

h = sa.H(); st = h.init()
fn, chan, ctrl = h.live_channel()
print("channel:", hex(chan) if chan else None, "controller:", hex(ctrl) if ctrl else None)
if not chan:
    raise SystemExit(1)
vt = h.rd64(chan)
print("vtable:", hex(vt))
# 0x808/8 = 257
for slot_byte in (0x808,):
    ptr = h.rd64(vt + slot_byte)
    print(f"vtable+{slot_byte:#x} -> {ptr:#x} (rva {ptr - h.mod:#x})")
# 也打印附近几个槽位
for off in range(0x7e0, 0x840, 8):
    try:
        p = h.rd64(vt + off)
        if h.mod <= p < h.mod + 0x8000000:
            print(f"  slot {off:#x} -> {p:#x}")
    except Exception:
        pass
