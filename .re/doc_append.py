# -*- coding: utf-8 -*-
import io, os

README = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\README.md"
section = """

---

## 15. 管理员命令全链路（2026-11-20 打通）

### 15.1 命令入口与正确调用方式

- 函数：`Chat_Server_ProcessAdminCommand(commandText)`，宿主类是 **`PlayerRpcChannel`**（不是 PlayerController）
- **参数必须去掉 `#` 前缀**：服务端解析的是裸命令名
  - 正确：`Announce 123`、`Teleport -660000 -270000 12000 Ac`
  - 错误：`#Announce 123`（服务端回 `Unrecognized command.`）
  - 依据：玩家手打 `#Announce 123` 时服务端日志为 `Command: 'Announce 123'`（`#` 由客户端剥掉）
- 通道选择：`findbyclassnameid <PlayerRpcChannel 类名id>` → 取**对象索引最大**的实例（最新创建 = 当前在线玩家），其 `+0x20` 即 owner PlayerController
- 调用：`gtcallpe <fn 地址> <channel 地址> 0:s:"<command>"`

### 15.2 玩家对象定位

- 控制器：活通道 `+0x20`
- 角色 Pawn：控制器内存中类名 `BP_Prisoner_C` 的对象（实测偏移 `+0x250/+0x260/+0x2a0/+0x760/+0x790`）
- 坐标读取：`pawn+0x130` → RootComponent；`root+0x1D0` → FVector 世界坐标（cm）

### 15.3 管理员权限检查（静态结论）

| 项 | 值 |
|---|---|
| 分发函数 | `PlayerRpcChannel` vtable+0x808，RVA `0x1F4FED0` |
| 参数来源 | `0x1AA0C90` = `lea rax,[rcx+0x6C8]; ret` → 控制器内 FString 成员（SteamID） |
| 检查函数 | RVA `0x1F8D8C0`，**AL=1 是管理员，AL=0 不是**（TSet 字符串查表） |
| 分发处判定 | `test r15b,r15b; je <拒绝分支 0x1F5005B>` |
| FString 布局 | `+0x00 data 指针 / +0x08 Num（**含结尾 NUL**）/ +0x0C Max` |

### 15.4 定向放行（只让指定 SteamID 通过，无需 AdminUsers.ini）

- 钩子：在 RVA `0x1F8D8C0` 首 5 字节写 `E9 rel32` → 桩
- 桩逻辑：调过滤器比较 FString 与目标 SteamID
  - 命中 → `mov eax,1; ret`（判定为管理员）
  - 未命中 → 跳板（原始 5 字节 `48 89 5C 24 10` + 跳回 target+5）→ 走原始逻辑
- **约束 1（崩溃根因）**：桩/跳板必须分配在 target **±2GB** 内，否则 `E9 rel32` 溢出被截断 →
  `EXCEPTION_ACCESS_VIOLATION 0x7ff68a0d0000`（低 32 位与桩地址一致可佐证）
- **约束 2**：`FString.Num` 含 NUL，比较长度须接受 `len` 或 `len+1`
- **约束 3**：`je` 相对偏移必须精确（曾写 `+7` 跳进 `movabs` 中间导致崩溃）
- 持久化：`Binaries\\Win64\\scum_harness_admin.txt` 存 SteamID，插件启动自动 `setadmintarget` + `installadm`
- 相关命令：`setadmintarget <steamid>` / `installadm` / `admstate` / `writemem <addr> <hex>` / `patchret1 <addr>`
- **`AdminUsers.ini` 必须为空**（纯文本、无 BOM）；若写入 SteamID 等于对所有人生效

### 15.5 命令清单来源

- 对象表内全部 `AdminCommand_*` 类 = 命令全集（本版本 222 条）：`python scum_admin.py --list`
- 常用：
  - `Announce <消息>`
  - `Teleport <X> <Y> <Z> [玩家]`（**坐标在前、玩家在后**；不带玩家=自己）
  - `SpawnItem <物品> [数量]`
  - `SetGodMode <True/False>`、`SetPrisonerImmortality <0/1>`
  - `ListPlayers`、`MutePlayer`、`KickPlayer`、`BanPlayer` 等
- 物品名：带 `_ES` 后缀的是事件限定版，**不允许刷**（`Phoenix_Tears_ES` → not allowed）；
  普通版可刷：`Phoenix_Tears`、`Apple`、`Painkillers_01`…

### 15.6 客户端工具

- `client/scum_admin.py`
  - `python scum_admin.py "Announce hello"` 发任意命令（自动去 `#`、自动选最新通道）
  - `python scum_admin.py --list` 列出全部命令类
  - `python scum_admin.py --tp <dx> <dy> [玩家]` 相对当前位置传送
- `client/scumctl.py` 底层原始命令通道

### 15.7 启动配方（含钩子自动安装）

1. 确认 `Binaries\\Win64\\scum_harness_admin.txt` 里是要放行的 SteamID
2. 确认 `Saved\\Config\\WindowsServer\\AdminUsers.ini` 为空
3. 启动服务端（黑窗口）：`D:\\SCUM_Server\\start_server.bat`
4. 日志 `Binaries\\Win64\\scum_harness.log` 应出现：
   `[admhook] installed: target=... stub=... tramp=...` + `[admhook] auto-installed for <id>`
5. `python scumctl.py admstate` → `hooked:true, target:<id>`
"""

with open(README, "a", encoding="utf-8") as f:
    f.write(section)
print("appended", len(section), "chars; file size now", os.path.getsize(README))
