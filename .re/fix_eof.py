# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()
old = '''        if (!CbReadWhole(full, from, chunk, newSize)) continue;
        g_logOffsets[name] = newSize;
        if (chunk.empty()) continue;'''
new = '''        if (!CbReadWhole(full, from, chunk, newSize)) continue;
        // 注意：不要在这里推进偏移！只有真正提交了行之后才推进，
        // 否则"没有换行符的末行"会在首个周期被跳过而永久丢失。
        if (chunk.empty()) continue;'''
assert old in s, "offset-advance line not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
