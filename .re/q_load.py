
import json
fns = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\functions2.json"))
def grep(kw):
    return [(f["o"], f["f"]) for f in fns if kw.lower() in f["f"].lower()]
for kw in ["LoadAsset","LoadObject","LoadClass","LoadStreamLevel","StreamLevel"]:
    hits = grep(kw)
    print("==", kw, len(hits))
    for o,f in hits[:12]: print("   %s.%s" % (o,f))
print()
print("KismetSystemLibrary sample:", [f["f"] for f in fns if f["o"]=="KismetSystemLibrary"][:25])
