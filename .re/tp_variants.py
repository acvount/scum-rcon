import json, socket, struct, time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scum-harness", "client"))
import scum_admin as sa

h = sa.H(); st = h.init()
fn, chan, ctrl = h.live_channel()
pawn, _ = h.find_pawn(chan)
print("channel:", hex(chan) if chan else None, "pawn:", hex(pawn) if pawn else None)
if not pawn:
    raise SystemExit(1)
cur = h.pawn_loc(pawn)
print("current:", cur)
tx = cur[0] + 15000; ty = cur[1] + 15000; tz = cur[2] + 150
variants = [
    f"#Teleport Ac {tx:.0f} {ty:.0f} {tz:.0f}",
    f"#Teleport {tx:.0f} {ty:.0f} {tz:.0f}",
    f"#Teleport Ac {tx:.1f} {ty:.1f} {tz:.1f}",
]
for v in variants:
    print("\n>>>", v)
    r = h.exec_admin(v)
    print("   ", json.dumps(r, ensure_ascii=False))
    time.sleep(2)
    try:
        now = h.pawn_loc(pawn)
        print("   loc:", now)
        if abs(now[0] - cur[0]) > 100 or abs(now[1] - cur[1]) > 100:
            print("   *** 传送成功 ***")
            break
    except Exception as e:
        print("   recheck fail:", e)
