
import json
fns = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\functions2.json"))
for kw in ["SpawnPlayer","PlayerControllerClass","RestartPlayer","Login","CreatePlayer"]:
    hits = [(f["o"], f["f"]) for f in fns if kw.lower() in f["f"].lower()]
    print("==", kw, len(hits))
    for o,f in hits[:10]: print("   %s.%s" % (o,f))
