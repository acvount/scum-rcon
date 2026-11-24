# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

old = '''    for (int i2 = 0; i2 < nc; ++i2) {
        std::string sid = CbReadFString((uint8_t*)candidates[i2] + 0x6C8);'''
new = '''    if (nc > 0) {
        uint64_t q0 = 0, q1 = 0;
        for (int k = 0; k < nc && k < 2; ++k) {
            uint64_t q = 0;
            if (MemReadable((uint8_t*)candidates[k] + 0x6C8, 8)) q = *(uint64_t*)((uint8_t*)candidates[k] + 0x6C8);
            if (k == 0) q0 = q; else q1 = q;
        }
        Log("[cb] dbg ctx=%p nc=%d c0=%p q0=%p c1=%p q1=%p", ctx, nc, candidates[0], (void*)q0,
            nc > 1 ? candidates[1] : nullptr, (void*)q1);
    }
    for (int i2 = 0; i2 < nc; ++i2) {
        std::string sid = CbReadFString((uint8_t*)candidates[i2] + 0x6C8);'''
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched")
