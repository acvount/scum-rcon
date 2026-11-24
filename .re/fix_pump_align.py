# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

old = '''        std::string pending = g_logPending[name];
        chunk = pending + chunk;
        g_logPending[name].clear();
        if (chunk.empty()) continue;
        // 文件名 -> 类型（前缀到第一个数字前）
        std::string type = name;
        size_t u = type.find('_');
        if (u != std::string::npos) type = type.substr(0, u);
        // UTF-16LE 解码（保证偶数长度）
        size_t n = chunk.size() / 2;
        const wchar_t* w = (const wchar_t*)chunk.data();
        std::string line;
        for (size_t i = 0; i < n; ++i) {
            wchar_t c = w[i];
            if (c == L'\\n') { CbEmitLogLine(type, name, line); line.clear(); }
            else if (c != L'\\r') {
                if (c < 128) line += (char)c;
                else line += CbUtf16ToUtf8(&c, 1);
            }
        }
        if (!line.empty()) g_logPending[name] = line;   // 尾部半行留到下次'''

new = '''        if (chunk.empty()) continue;
        // 只处理完整 wchar（偶数长度），且只推进到最后一个换行为止
        size_t usable = chunk.size() & ~(size_t)1;
        if (usable < 2) { g_logOffsets[name] = from; continue; }
        std::string type = name;
        size_t u = type.find('_');
        if (u != std::string::npos) type = type.substr(0, u);
        size_t n = usable / 2;
        const wchar_t* w = (const wchar_t*)chunk.data();
        // 先找最后一个 '\\n' 的字符下标
        size_t lastNl = (size_t)-1;
        for (size_t i = n; i > 0; --i) {
            if (w[i - 1] == L'\\n') { lastNl = i - 1; break; }
        }
        if (lastNl == (size_t)-1) { g_logOffsets[name] = from; continue; }   // 没有完整行
        std::string line;
        for (size_t i = 0; i <= lastNl; ++i) {
            wchar_t c = w[i];
            if (c == L'\\n') { CbEmitLogLine(type, name, line); line.clear(); }
            else if (c != L'\\r') {
                if (c < 128) line += (char)c;
                else line += CbUtf16ToUtf8(&c, 1);
            }
        }
        g_logOffsets[name] = from + (unsigned long long)(lastNl + 1) * 2;'''
assert old in s, "pump block not found"
s = s.replace(old, new, 1)

# 移除不再使用的 pending 声明与赋值处引用（保留声明但不用无妨）；这里直接删除声明
s = s.replace('static std::map<std::string, std::string> g_logPending;   // 跨块半行缓存\n', '')

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
