# -*- coding: utf-8 -*-
PATH = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
MOD = r"C:\Users\Administrator\Desktop\逆向scumserver\.re\cb_module.txt"

src = open(PATH, "r", encoding="utf-8", errors="surrogateescape").read()
mod = open(MOD, "r", encoding="utf-8").read()

if "CbWorker" in src:
    print("already inserted")
    raise SystemExit(0)

# 1) 插入模块（在 CmdFindByOuter 之前）
anchor = 'static std::string CmdFindByOuter(const std::vector<std::string>& a) {'
assert anchor in src, "anchor CmdFindByOuter missing"
src = src.replace(anchor, mod + anchor, 1)

# 2) 命令分发
d = '    if (cmd == "admstate") return CmdAdmState(a);'
assert d in src, "dispatch anchor missing"
src = src.replace(d, d + '\n    if (cmd == "cbreload") return CmdCbReload(a);'
                        '\n    if (cmd == "cbtest") return CmdCbTest(a);'
                        '\n    if (cmd == "cbstate") return CmdCbState(a);', 1)

# 3) 启动初始化（配置 + 挂钩 + worker）
init_old = '''        __try { LoadAdminTargetAndHook(); }
        __except (EXCEPTION_EXECUTE_HANDLER) { Log("[admhook] exception during auto-install"); }
    }'''
init_new = '''        __try { LoadAdminTargetAndHook(); }
        __except (EXCEPTION_EXECUTE_HANDLER) { Log("[admhook] exception during auto-install"); }
        __try {
            CbReloadConfig();
            InstallChatHook();
            std::thread(CbWorker).detach();
            Log("[cb] worker started");
        } __except (EXCEPTION_EXECUTE_HANDLER) { Log("[cb] init exception"); }
    }'''
assert init_old in src, "init anchor missing"
src = src.replace(init_old, init_new, 1)

open(PATH, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("inserted ok, size", len(src))
