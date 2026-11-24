
import json, collections
fns = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\functions.json"))
print("total:", len(fns))
owners = collections.Counter(f["o"] for f in fns)
print("top owners:", owners.most_common(20))
def grep(kw):
    return [(f["o"], f["f"]) for f in fns if kw.lower() in f["f"].lower()]
for kw in ["Notification","Item","Inventory","Spawn","Announce","Message"]:
    hits = grep(kw)
    print("\n== %s (%d)" % (kw, len(hits)))
    for o,f in hits[:12]: print("   %s.%s" % (o,f))
