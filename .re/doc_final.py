# -*- coding: utf-8 -*-
README = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\README.md"
section = """

### 15.9 最终方案：按"调用来源"放行（实测通过 2026-11-20 23:26）

**需求**：本地工具发起的命令必须永远能执行（不依赖任何 SteamID / 管理员名单）；
游戏内玩家自己打 `#` 命令仍严格按 `AdminUsers.ini` 校验。

**实现**：在钩子过滤器最前面加"调用来源"判定
```cpp
static volatile LONG g_injectDepth = 0;   // 本工具调用计数

// CmdGtCallImpl 里：投递任务前置位，等待返回后清位
InterlockedIncrement(&g_injectDepth);
InterlockedExchange(&g_loadRec.state, 0);
/* 等待 state==2 */
InterlockedDecrement(&g_injectDepth);

// 过滤器入口
if (InterlockedCompareExchange(&g_injectDepth, 0, 0) > 0) return 1;  // 本地工具 → 直接放行
```

**三种来源的行为**
| 来源 | 检查结果 | 说明 |
|---|---|---|
| 本工具注入调用（`gtcall`/`gtcallpe`） | 1（放行） | 不看 SteamID、不看名单 |
| 名单内的玩家在游戏里打 `#命令` | 走原始检查 → 1 | 由 `AdminUsers.ini` 决定 |
| 名单外的玩家 | 走原始检查 → 0 | 拒绝 |

**验证证据**（目标 ID = 假值 `11111111111111111`，`AdminUsers.ini` 为空）
```
'76561199558480354:Ac(1)[DEV]' Command: 'Announce YG-LOCAL-TOOL-PASS-1'
'76561199558480354:Ac(1)[DEV]' Command: 'Announce YG-LOCAL-TOOL-PASS-2'
```
- `[DEV]` 后缀 = 检查返回 1（16 处调用点里那处日志分支）
- 玩家端确认收到公告

**另一个坑：通道选择必须选"活的"那个**
- 玩家重连后会留下旧通道对象；按"对象索引最大"选会选到过期通道，命令不会进服务端
- 症状：客户端 `ex=0` 但服务端日志里**没有** `Command:` 行
- 正确做法：通道打分 = `owner 类名含 PlayerController(2 分)` + `能量到 pawn(5 分)`，取最高分；
  仍平手时取索引最大者

### 15.10 聊天频道类型（`EChatType` 枚举，实测）

| 值 | 名称 | 显示 |
|---|---|---|
| 0 | Default | 同 Local（白色附近） |
| 1 | Local | 白色，附近范围 |
| 2 | **Global** | **蓝色全频道** |
| 3 | Squad | 队伍 |
| 4 | Admin | 管理员频道 |
| 5 | CommandsOnly | 仅命令回显 |
| 6 | ServerMessage | 服务器消息 |
| 7 | Error | 错误 |

- 取法：对象表里 `findclass Enum` → 名字含 `Chat` 的 `EChatType`（UEnum，`Names` 数组在 `+0x40`，
  每项 `{FName id(4B), 4B pad, int64 value}`）
- 发送：`BroadcastChatLine(WorldContextObject, Text, ChatType)`，如
  `python scum_chat.py "[YG] 全频道广播" --chattype 2`
"""

with open(README, "a", encoding="utf-8") as f:
    f.write(section)
print("ok")
