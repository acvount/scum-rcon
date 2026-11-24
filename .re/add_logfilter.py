# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

old = '''    std::string dir = CbLogsDir();
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA((dir + "\\\\*_*.log").c_str(), &fd);
    std::string out = "{\\"ok\\":true,\\"dir\\":\\"" + CbJsonEsc(dir) + "\\",\\"files\\":[";'''
new = '''    std::string dir = CbLogsDir();
    std::string prefix = a.size() > 1 ? a[1] : "";
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA((dir + "\\\\" + (prefix.empty() ? std::string("*_*.log") : prefix + "_*.log")).c_str(), &fd);
    std::string out = "{\\"ok\\":true,\\"dir\\":\\"" + CbJsonEsc(dir) + "\\",\\"files\\":[";'''
assert old in s, "diag header not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
