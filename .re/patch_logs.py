# -*- coding: utf-8 -*-
PATH = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
MOD = r"C:\Users\Administrator\Desktop\逆向scumserver\.re\cb_logs_module.txt"

src = open(PATH, "r", encoding="utf-8", errors="surrogateescape").read()
if "CbLogWorker" in src:
    print("already inserted")
    raise SystemExit(0)

mod = open(MOD, "r", encoding="utf-8").read()

# 插到 "// 聊天事件采集" 之前（保持同文件顺序：仍在使用 CbPush/CbJsonEsc 之后定义）
anchor = "// 聊天事件采集（在 exec 入口调用"
assert anchor in src, "anchor not found"
src = src.replace(anchor, mod + "\n" + anchor, 1)

# 启动时启动日志线程
old = '''        std::thread(CbWorker).detach();
        Log("[cb] worker started");'''
new = '''        std::thread(CbWorker).detach();
        Log("[cb] worker started");
        std::thread(CbLogWorker).detach();
        Log("[cblog] log worker started");'''
assert old in src
src = src.replace(old, new, 1)

# cbstate 里加上日志计数
old2 = ',\\"chatHooked\\":" + (g_chatStub ? "true" : "false") + "}";'
new2 = ',\\"chatHooked\\":" + (g_chatStub ? "true" : "false") + ",\\"logEvents\\":" + std::to_string(g_logEvents) + "}";'
assert old2 in src, "cbstate anchor missing"
src = src.replace(old2, new2, 1)

open(PATH, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("inserted")
