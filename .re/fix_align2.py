# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

# 1) 基线：偶数对齐
old1 = 'if (GetFileSizeEx(f, &sz)) g_logOffsets[name] = (unsigned long long)sz.QuadPart;'
new1 = 'if (GetFileSizeEx(f, &sz)) g_logOffsets[name] = ((unsigned long long)sz.QuadPart) & ~1ULL;'
assert old1 in s, "baseline assign not found"
s = s.replace(old1, new1, 1)

# 2) 泵：读之前把 from 对齐到偶数
old2 = '''        unsigned long long from = 0;
        auto it = g_logOffsets.find(name);
        if (it != g_logOffsets.end()) from = it->second;'''
new2 = '''        unsigned long long from = 0;
        auto it = g_logOffsets.find(name);
        if (it != g_logOffsets.end()) from = it->second;
        from &= ~1ULL;                       // UTF-16 必须偶数对齐'''
assert old2 in s, "pump from-read not found"
s = s.replace(old2, new2, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
