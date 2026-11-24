# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

if "CbEmitLogin" in s:
    print("already"); raise SystemExit(0)

# 在 CbEmitLogLine 之前插入 login/logout 专用解析
anchor = "static void CbEmitLogLine(const std::string& type, const std::string& fileName, const std::string& line) {"
parser = r'''// login / logout 行结构化：
// '192.168.1.112 76561199558480354:Ac(1)' logged in at: X=-644362.000 Y=-260984.000 Z=14534.000
static bool CbEmitLogin(const std::string& type, const std::string& fileName,
                        const std::string& ts, const std::string& text) {
    (void)fileName;
    size_t q1 = text.find('\'');
    size_t q2 = (q1 == std::string::npos) ? std::string::npos : text.find('\'', q1 + 1);
    if (q1 == std::string::npos || q2 == std::string::npos) return false;
    std::string who = text.substr(q1 + 1, q2 - q1 - 1);   // "ip steamid:name(n)"
    std::string ip, sid, name;
    size_t sp = who.find(' ');
    if (sp != std::string::npos) { ip = who.substr(0, sp); who = who.substr(sp + 1); }
    size_t c1 = who.find(':');
    if (c1 == std::string::npos) return false;
    sid = who.substr(0, c1);
    std::string nm = who.substr(c1 + 1);
    size_t par = nm.find('(');
    name = (par == std::string::npos) ? nm : nm.substr(0, par);

    std::string action = "login";
    if (text.find("logged out") != std::string::npos) action = "logout";
    else if (text.find("logged in") == std::string::npos) return false;

    std::string pos;
    size_t x = text.find("X=");
    if (x != std::string::npos) pos = text.substr(x);
    for (auto& ch : pos) if (ch == ' ') ch = ',';

    std::string json = "{\"event\":\"login\",\"steamID\":\"" + CbJsonEsc(sid) +
                       "\",\"fackname\":\"" + CbJsonEsc(name) +
                       "\",\"steamname\":\"" + CbJsonEsc(name) +
                       "\",\"date\":\"" + CbJsonEsc(ts) +
                       "\",\"data\":{\"action\":\"" + action + "\",\"ip\":\"" + CbJsonEsc(ip) +
                       "\",\"position\":\"" + CbJsonEsc(pos) + "\",\"source\":\"log\"}}";
    CbPush(json);
    ++g_logEvents;
    return true;
}

'''
assert anchor in s
s = s.replace(anchor, parser + anchor, 1)

# 在 CbEmitLogLine 的 chat 分支之前，先处理 login
old = '''    if (type == "chat") {'''
new = '''    if (type == "login" || type == "admin") {
        if (CbEmitLogin(type, fileName, ts, text)) return;
    }
    if (type == "chat") {'''
assert old in s
s = s.replace(old, new, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
