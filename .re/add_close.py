# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()
old = 'std::wstring hdr = L"Content-Type: application/json; charset=utf-8\\r\\n";'
new = 'std::wstring hdr = L"Content-Type: application/json; charset=utf-8\\r\\nConnection: close\\r\\n";'
assert old in s, "header line not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
