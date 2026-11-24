# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

if "CbFixWide" in s:
    print("already there"); raise SystemExit(0)

anchor = "static std::string CbJsonEsc(const std::string& s) {"
helper = r'''// 编码回滚：游戏服务端把 UTF-8 字节按 GBK 解码，导致"你好"→"浣犲ソ"。
// 做法：把 wchar 按 GBK 编码回字节，再按 UTF-8 解码；成功则采用（即原始文本），
// 失败说明本来就是真中文，保留原样。
static std::string CbFixWide(const wchar_t* s, int n) {
    if (!s || n <= 0) return "";
    bool hasCjk = false;
    for (int i = 0; i < n; ++i) {
        unsigned int c = (unsigned int)s[i];
        if (c >= 0x4E00 && c <= 0x9FFF) { hasCjk = true; break; }
    }
    if (hasCjk) {
        int cb = WideCharToMultiByte(936, 0, s, n, nullptr, 0, nullptr, nullptr);
        if (cb > 0) {
            std::string gbk((size_t)cb, '\0');
            WideCharToMultiByte(936, 0, s, n, &gbk[0], cb, nullptr, nullptr);
            int wl = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, gbk.data(), cb, nullptr, 0);
            if (wl > 0) {
                std::wstring w((size_t)wl, L'\0');
                MultiByteToWideChar(CP_UTF8, 0, gbk.data(), cb, &w[0], wl);
                return CbUtf16ToUtf8(w.c_str(), wl);
            }
        }
    }
    return CbUtf16ToUtf8(s, n);
}

'''
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)

# CaptureChat 里改用 CbFixWide
old = '''    if (msg && msgLen > 1 && msgLen < 2000 && MemReadable(msg, (size_t)msgLen * 2))
        msgU8 = CbUtf16ToUtf8(msg, msgLen - 1);'''
new = '''    if (msg && msgLen > 1 && msgLen < 2000 && MemReadable(msg, (size_t)msgLen * 2))
        msgU8 = CbFixWide(msg, msgLen - 1);'''
assert old in s, "capture msg not found"
s = s.replace(old, new, 1)

# 日志行构建：把整行先转 wstring 再统一回滚
old2 = '''        std::string line;
        for (size_t i = 0; i <= lastNl; ++i) {
            wchar_t c = w[i];
            if (c == L'\\n') { CbEmitLogLine(type, name, line); line.clear(); }
            else if (c != L'\\r') {
                if (c < 128) line += (char)c;
                else line += CbUtf16ToUtf8(&c, 1);
            }
        }'''
new2 = '''        std::wstring wline;
        for (size_t i = 0; i <= lastNl; ++i) {
            wchar_t c = w[i];
            if (c == L'\\n') {
                CbEmitLogLine(type, name, CbFixWide(wline.c_str(), (int)wline.size()));
                wline.clear();
            } else if (c != L'\\r') {
                wline += c;
            }
        }'''
assert old2 in s, "line build not found"
s = s.replace(old2, new2, 1)

# 尾部两条路径同样处理
old3 = '''                std::string tail;
                for (size_t i = lastNl + 1; i < n; ++i) {
                    wchar_t c = w[i];
                    if (c == L'\\n' || c == L'\\r') continue;
                    if (c < 128) tail += (char)c;
                    else tail += CbUtf16ToUtf8(&c, 1);
                }
                if (!tail.empty()) CbEmitLogLine(type, name, tail);'''
new3 = '''                std::wstring wtail;
                for (size_t i = lastNl + 1; i < n; ++i) {
                    wchar_t c = w[i];
                    if (c == L'\\n' || c == L'\\r') continue;
                    wtail += c;
                }
                if (!wtail.empty()) CbEmitLogLine(type, name, CbFixWide(wtail.c_str(), (int)wtail.size()));'''
assert old3 in s, "tail1 not found"
s = s.replace(old3, new3, 1)

old4 = '''                std::string tail;
                for (size_t i = 0; i < n; ++i) {
                    wchar_t c = w[i];
                    if (c == L'\\n' || c == L'\\r') continue;
                    if (c < 128) tail += (char)c;
                    else tail += CbUtf16ToUtf8(&c, 1);
                }
                if (tail.empty()) { g_logOffsets[name] = from + (unsigned long long)usable; }
                else {
                    CbEmitLogLine(type, name, tail);'''
new4 = '''                std::wstring wtail;
                for (size_t i = 0; i < n; ++i) {
                    wchar_t c = w[i];
                    if (c == L'\\n' || c == L'\\r') continue;
                    wtail += c;
                }
                std::string tail = CbFixWide(wtail.c_str(), (int)wtail.size());
                if (tail.empty()) { g_logOffsets[name] = from + (unsigned long long)usable; }
                else {
                    CbEmitLogLine(type, name, tail);'''
assert old4 in s, "tail2 not found"
s = s.replace(old4, new4, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
