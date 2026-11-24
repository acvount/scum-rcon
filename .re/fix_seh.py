# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()
old = '''        __try {
            CbReloadConfig();
            InstallChatHook();
            std::thread(CbWorker).detach();
            Log("[cb] worker started");
        } __except (EXCEPTION_EXECUTE_HANDLER) { Log("[cb] init exception"); }'''
new = '''        CbReloadConfig();
        InstallChatHook();
        std::thread(CbWorker).detach();
        Log("[cb] worker started");'''
if old in s:
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("fixed")
else:
    print("pattern not found; showing region:")
    i = s.find("CbReloadConfig();")
    print(s[max(0, i - 300):i + 300])
