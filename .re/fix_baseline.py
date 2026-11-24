# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

# 1) 时间戳解析：支持 ":  " 与 ": "
old = '''    std::string ts, text;
    size_t sep = s.find(":  ");
    if (sep != std::string::npos && sep < 32) { ts = s.substr(0, sep); text = s.substr(sep + 3); }
    else { ts = CbNowStamp(); text = s; }'''
new = '''    std::string ts, text;
    // 行首形如 "2026.11.21-02.34.27: <text>" 或 "...:  <text>"（1~2 个空格）
    size_t sep = std::string::npos, skip = 0;
    if (s.size() > 12 && s[4] == '.' && s[7] == '.' && s[10] == '-') {
        size_t c = s.find(':', 11);
        if (c != std::string::npos && c < 32) {
            sep = c;
            skip = 1;
            while (c + skip < s.size() && s[c + skip] == ' ') ++skip;
        }
    }
    if (sep != std::string::npos) { ts = s.substr(0, sep); text = s.substr(sep + skip); }
    else { ts = CbNowStamp(); text = s; }'''
assert old in s, "ts parse not found"
s = s.replace(old, new, 1)

# 2) 基线提前：BootThread 里先建基线
old2 = '''static DWORD WINAPI BootThread(LPVOID) {
    ServerThread();
    return 0;
}'''
new2 = '''static DWORD WINAPI BootThread(LPVOID) {
    __try { CbLogBaseline(); }          // 立即建基线，避免漏掉加载期间的登录/聊天
    __except (EXCEPTION_EXECUTE_HANDLER) { Log("[cblog] early baseline exception"); }
    ServerThread();
    return 0;
}'''
assert old2 in s, "BootThread not found"
s = s.replace(old2, new2, 1)

# 3) 日志线程里不再重复建基线
old3 = '''static void CbLogWorker() {
    CbLogBaseline();'''
new3 = '''static void CbLogWorker() {
    if (g_logOffsets.empty()) CbLogBaseline();'''
assert old3 in s, "worker baseline not found"
s = s.replace(old3, new3, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
