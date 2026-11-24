# -*- coding: utf-8 -*-
p = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()

# 1) 新增一个不带展开对象的 SEH 包装函数（放在 LoadAdminTargetAndHook 之后）
anchor = '''    if (InstallAdminHook()) Log("[admhook] auto-installed for %s", id.c_str());
    else Log("[admhook] auto-install FAILED (prologue mismatch?)");
}'''
assert anchor in s
wrapper = anchor + '''

// 单独包一层 SEH（InitWorker 里有 std::thread 等需要展开的对象，不能直接 __try）
static void LoadAdminGuarded() {
    __try { LoadAdminTargetAndHook(); }
    __except (EXCEPTION_EXECUTE_HANDLER) { Log("[admhook] exception during auto-install"); }
}'''
s = s.replace(anchor, wrapper, 1)

# 2) InitWorker 里替换掉 __try 块
old = '''        __try { LoadAdminTargetAndHook(); }
        __except (EXCEPTION_EXECUTE_HANDLER) { Log("[admhook] exception during auto-install"); }
'''
assert old in s
s = s.replace(old, '        LoadAdminGuarded();\n', 1)

open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("ok")
