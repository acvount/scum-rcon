# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

# 1) 增加 per-file 半行缓存
old_decl = 'static std::map<std::string, unsigned long long> g_logOffsets;'
new_decl = old_decl + '\nstatic std::map<std::string, std::string> g_logPending;   // 跨块半行缓存'
assert old_decl in s
s = s.replace(old_decl, new_decl, 1)

# 2) 正文去掉 "ts:  " 前缀
old_emit = '''    std::string ts, text;
    size_t sep = s.find(":  ");
    if (sep != std::string::npos && sep < 32) { ts = s.substr(0, sep); text = s.substr(sep + 3); }
    else { ts = CbNowStamp(); text = s; }'''
new_emit = '''    std::string ts, text;
    size_t sep = s.find(":  ");
    if (sep != std::string::npos && sep < 32) { ts = s.substr(0, sep); text = s.substr(sep + 3); }
    else { ts = CbNowStamp(); text = s; }
    // 文本里若仍带 "ts:  " 前缀则剥离（避免重复）
    if (text.size() > sep + 3 && text.compare(0, ts.size(), ts) == 0) {
        size_t q = text.find(":  ");
        if (q != std::string::npos && q < 32) text = text.substr(q + 3);
    }'''
assert old_emit in s
s = s.replace(old_emit, new_emit, 1)

# 3) 泵里拼接 pending 并保留尾部半行
old_pump = '''        if (chunk.empty()) continue;
        // 文件名 -> 类型（前缀到第一个数字前）
        std::string type = name;
        size_t u = type.find('_');
        if (u != std::string::npos) type = type.substr(0, u);
        // UTF-16LE 解码
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
        }'''
new_pump = '''        std::string pending = g_logPending[name];
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
assert old_pump in s, "pump block not found"
s = s.replace(old_pump, new_pump, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
