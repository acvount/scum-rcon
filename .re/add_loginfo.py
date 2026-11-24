# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()
if "CmdCbLogInfo" in s:
    print("already there"); raise SystemExit(0)

anchor = "static void CbLogWorker() {"
diag = r'''static std::string CmdCbLogInfo(const std::vector<std::string>& a) {
    (void)a;
    std::string dir = CbLogsDir();
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA((dir + "\\*_*.log").c_str(), &fd);
    std::string out = "{\"ok\":true,\"dir\":\"" + CbJsonEsc(dir) + "\",\"files\":[";
    if (h != INVALID_HANDLE_VALUE) {
        int n = 0;
        do {
            std::string name = fd.cFileName;
            unsigned long long real = 0;
            HANDLE f = CreateFileA((dir + "\\" + name).c_str(), GENERIC_READ,
                                   FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, 0, nullptr);
            if (f != INVALID_HANDLE_VALUE) {
                LARGE_INTEGER sz;
                if (GetFileSizeEx(f, &sz)) real = (unsigned long long)sz.QuadPart;
                CloseHandle(f);
            } else {
                continue;
            }
            unsigned long long off = 0;
            auto it = g_logOffsets.find(name);
            if (it != g_logOffsets.end()) off = it->second;
            std::string type = name;
            size_t u = type.find('_');
            if (u != std::string::npos) type = type.substr(0, u);
            if (n) out += ",";
            ++n;
            out += "{\"name\":\"" + CbJsonEsc(name) + "\",\"type\":\"" + CbJsonEsc(type) +
                   "\",\"size\":" + std::to_string(real) + ",\"offset\":" + std::to_string(off) +
                   ",\"lag\":" + std::to_string(real > off ? real - off : 0) + "}";
            if (n >= 60) break;
        } while (FindNextFileA(h, &fd));
        FindClose(h);
    }
    out += "]}";
    return out;
}

'''
assert anchor in s
s = s.replace(anchor, diag + anchor, 1)

d = '    if (cmd == "cbstate") return CmdCbState(a);'
assert d in s
s = s.replace(d, d + '\n    if (cmd == "cbloginfo") return CmdCbLogInfo(a);', 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
