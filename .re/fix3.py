PATH = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
raw = open(PATH, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]
lines = raw.decode("utf-8", "surrogateescape").split("\n")

out = []
fixed = []
for ln in lines:
    # A) g_adminTarget 后塞了 g_adminStub
    if "g_adminStub = nullptr" in ln and "g_adminTarget" in ln:
        cut = ln.index("static void*")
        head = ln[:cut].rstrip()
        tail = ln[cut:]
        # tail 还可能带着 g_adminTramp
        if "g_adminTramp" in tail:
            c2 = tail.index("static void*        g_adminTramp")
            out.append(head)
            out.append(tail[:c2].rstrip())
            out.append(tail[c2:])
        else:
            out.append(head)
            out.append(tail)
        fixed.append("g_stub")
        continue
    # B) kMaxDist 被注释吞掉
    if "const uintptr_t kMaxDist" in ln and not ln.lstrip().startswith("const"):
        cut = ln.index("const uintptr_t kMaxDist")
        head = ln[:cut].rstrip()
        tail = ln[cut:]
        out.append(head)
        out.append("    " + tail)
        fixed.append("kMaxDist")
        continue
    out.append(ln)

open(PATH, "wb").write(b"\xef\xbb\xbf" + "\n".join(out).encode("utf-8", "surrogateescape"))
print("fixed:", fixed)
