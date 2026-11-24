# -*- coding: utf-8 -*-
import sys, os, time
sys.path.insert(0, r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\client")
import scum_admin as sa

h = sa.H(); h.init()
fn = None
for f in h.send("dumpfuncsraw").get("functions", []):
    if h.dn(f["nameId"]) == "Chat_Server_BroadcastChatMessage":
        fn = int(f["addr"]); break
chn, chan, ctrl = h.live_channel()
print("fn =", hex(fn) if fn else None, "chan =", hex(chan) if chan else None)
if not fn or not chan:
    raise SystemExit(1)
for msg in ("ascii-hook-test", "中文测试"):
    r = h.send('gtcallpe 0x%x 0x%x 0:s:"%s" 16:b:1' % (fn, chan, msg))
    print("call:", r)
    time.sleep(1)
time.sleep(2)
print("---- 接收端最后 4 条 ----")
p = r"C:\Users\Administrator\Desktop\逆向scumserver\.re\cb_events.log"
if os.path.exists(p):
    for line in open(p, encoding="utf-8").read().strip().split("\n")[-4:]:
        print(line)
