# -*- coding: utf-8 -*-
README = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\README.md"
section = """

### 15.8 更正与最终结论（实测通过）

以下三条是 15.4 里判断错误的地方，以本节为准：

**（1）检查函数语义：AL=1 才是管理员**
- `RVA 0x1F8D8C0` 返回 1 = 在管理员集合中；返回 0 = 不在
- 分发处 `test r15b,r15b; je 0x1F5005B`：AL=1 走正常分支，AL=0 走拒绝分支
- 该函数共 16 处调用点，`0x1F4FF6D` 那处只影响日志格式（`[DEV]` 后缀），
  真正的权限门在其他调用点（如 `0x1930391` 所在的命令执行函数）

**（2）`PtrReadable` 不能用于堆上的 FString 参数（关键坑）**
- `PtrReadable` 只覆盖 exe 的模块段，堆地址一律判假
- 症状：过滤器每次调用都走 `unreadable` 分支 → 恒返回 0 → 命令一直被拒
- 正确做法：用 `VirtualQuery` 判 `MEM_COMMIT` + 非 `PAGE_NOACCESS/PAGE_GUARD`
- 诊断日志（已内置，前 40 次调用）：
  `[admfilter] #N ptr=... n=18 str='76561199558480354'` → `[admfilter] #N -> 1`

**（3）`FString.Num` 含结尾 NUL**
- 实测 `n=18` 而 SteamID 长度是 17；比较须接受 `want` 或 `want+1`

**最终验证（空 AdminUsers.ini，仅靠钩子）**
```
[admfilter] #35 ptr=000001F524AED3C8 n=18 str='76561199558480354'
[admfilter] #35 -> 1
```
→ 玩家收到公告 `YG-ONLY-ME-001` / `YG-ONLY-ME-002`，其他人仍被拒。

**完整生效条件清单**
1. `Binaries\\Win64\\scum_harness_admin.txt` = 目标 SteamID（无 BOM）
2. `Saved\\Config\\WindowsServer\\AdminUsers.ini` 为空
3. 插件启动日志出现 `[admhook] installed` + `[admhook] auto-installed for <id>`
4. 桩/跳板位于 target ±2GB（日志里的 stub/tramp 地址应为 `0x7FF6...`）
5. `python scumctl.py admstate` → `hooked:true`
"""

with open(README, "a", encoding="utf-8") as f:
    f.write(section)
print("ok")
