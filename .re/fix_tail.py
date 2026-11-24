# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

# 1) 新增两个跟踪表
anchor = 'static std::map<std::string, unsigned long long> g_logOffsets;'
assert anchor in s
if "g_logLastSize" not in s:
    s = s.replace(anchor, anchor + '''
static std::map<std::string, unsigned long long> g_logLastSize;   // 上次看到的大小
static std::map<std::string, int> g_logStable;                    // 大小不变计数''', 1)

# 2) 替换泵的文件处理段：加入"稳定即提交尾部"
old = '''        g_logOffsets[name] = from + (unsigned long long)(lastNl + 1) * 2;'''
new = '''        g_logOffsets[name] = from + (unsigned long long)(lastNl + 1) * 2;
        // 尾部若还有未换行的完整行：文件大小连续 2 个周期不变时提交
        unsigned long long tailFrom = g_logOffsets[name];
        size_t tailChars = (usable - (lastNl + 1) * 2) / 2;
        if (tailChars > 0) {
            unsigned long long prev = g_logLastSize.count(name) ? g_logLastSize[name] : 0;
            if (prev == newSize) { g_logStable[name] = g_logStable[name] + 1; }
            else { g_logLastSize[name] = newSize; g_logStable[name] = 0; }
            if (g_logStable[name] >= 2) {
                std::string tail;
                for (size_t i = lastNl + 1; i < n; ++i) {
                    wchar_t c = w[i];
                    if (c == L'\\n' || c == L'\\r') continue;
                    if (c < 128) tail += (char)c;
                    else tail += CbUtf16ToUtf8(&c, 1);
                }
                if (!tail.empty()) CbEmitLogLine(type, name, tail);
                g_logOffsets[name] = tailFrom + (unsigned long long)tailChars * 2;
            }
        } else {
            g_logLastSize[name] = newSize;
            g_logStable[name] = 0;
        }'''
assert old in s, "offset advance line not found"
s = s.replace(old, new, 1)

# 3) 没有换行的情况：稳定时整块提交
old2 = '''        if (lastNl == (size_t)-1) { g_logOffsets[name] = from; continue; }   // 没有完整行'''
new2 = '''        if (lastNl == (size_t)-1) {
            unsigned long long prev2 = g_logLastSize.count(name) ? g_logLastSize[name] : 0;
            if (prev2 == newSize) { g_logStable[name] = g_logStable[name] + 1; }
            else { g_logLastSize[name] = newSize; g_logStable[name] = 0; }
            if (g_logStable[name] >= 2) {
                std::string tail;
                for (size_t i = 0; i < n; ++i) {
                    wchar_t c = w[i];
                    if (c == L'\\n' || c == L'\\r') continue;
                    if (c < 128) tail += (char)c;
                    else tail += CbUtf16ToUtf8(&c, 1);
                }
                if (tail.empty()) { g_logOffsets[name] = from + (unsigned long long)usable; }
                else {
                    CbEmitLogLine(type, name, tail);
                    g_logOffsets[name] = from + (unsigned long long)usable;
                }
            }
            continue;
        }'''
assert old2 in s, "no-newline branch not found"
s = s.replace(old2, new2, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
