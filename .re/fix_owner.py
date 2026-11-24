# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

old = '''    std::string steamId, name, fakeName;
    if (MemReadable((uint8_t*)ctx + 0xA0, 8)) {
        void* owner = *(void**)((uint8_t*)ctx + 0xA0);
        if (owner) {
            steamId = CbReadFString((uint8_t*)owner + 0x6C8);
            name = CbReadFString((uint8_t*)owner + 0x6E0);
            fakeName = CbReadFString((uint8_t*)owner + 0x740);
            if (fakeName.empty()) fakeName = name;
        }
    }'''
new = '''    std::string steamId, name, fakeName;
    // 候选 owner：ctx+0xA0 / ctx+0x20，再扫描 ctx 前 0x200 字节，
    // 逐个校验 +0x6C8 是否为 17 位数字（SteamID），命中即为控制器
    void* candidates[40];
    int nc = 0;
    for (int k = 0; k < 2; ++k) {
        uint32_t off = k == 0 ? 0xA0 : 0x20;
        if (MemReadable((uint8_t*)ctx + off, 8)) {
            void* v = *(void**)((uint8_t*)ctx + off);
            if (v) candidates[nc++] = v;
        }
    }
    if (MemReadable(ctx, 0x200)) {
        for (uint32_t off = 0; off + 8 <= 0x200 && nc < 40; off += 8) {
            void* v = *(void**)((uint8_t*)ctx + off);
            if (v) candidates[nc++] = v;
        }
    }
    for (int i2 = 0; i2 < nc; ++i2) {
        std::string sid = CbReadFString((uint8_t*)candidates[i2] + 0x6C8);
        if (sid.size() == 17) {
            bool digits = true;
            for (char c : sid) if (!isdigit((unsigned char)c)) digits = false;
            if (digits) {
                steamId = sid;
                name = CbReadFString((uint8_t*)candidates[i2] + 0x6E0);
                fakeName = CbReadFString((uint8_t*)candidates[i2] + 0x740);
                if (fakeName.empty()) fakeName = name;
                break;
            }
        }
    }'''
assert old in s, "capture block not found"
s = s.replace(old, new, 1)

# 诊断日志：记录 ctx 与前 3 个候选
old2 = '''    CbPush(json);
    Log("[cb] im %s: %.80s", steamId.c_str(), msgU8.c_str());'''
new2 = '''    CbPush(json);
    Log("[cb] im ctx=%p cand=%d sid=%s msg=%.60s", ctx, nc, steamId.c_str(), msgU8.c_str());'''
assert old2 in s
s = s.replace(old2, new2, 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
