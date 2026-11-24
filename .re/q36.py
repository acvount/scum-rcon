
import json
fns = json.load(open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\functions2.json"))
for kw in ["ToUpper","IsValid","GetGameTimeInSeconds","LoadClassAsset_Blocking"]:
    hits = [(f["o"], f["f"]) for f in fns if f["f"] == kw or f["f"].startswith(kw)]
    print(kw, "->", hits[:6])
print()
lib = [(f["o"], f["f"]) for f in fns if f["o"] == "KismetStringLibrary"]
print("KismetStringLibrary funcs:", len(lib), lib[:10])
