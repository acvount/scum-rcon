# -*- coding: utf-8 -*-
README = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\README.md"
section = """

---

## 16. 实时事件 → 本地队列 → HTTP 回调（2026-11-20）

### 16.1 配置文件

`D:\\SCUM_Server\\server\\SCUM\\Binaries\\Win64\\scum_callback.json`
```json
{
  "enable": true,
  "url": "http://127.0.0.1:8080/scum/event"
}
```
- `enable`：总开关
- `url`：回调地址（当前实现支持 **http://**；HTTPS 未接）
- 运行期改配置后执行 `python scumctl.py cbreload` 即时生效，无需重启

### 16.2 事件结构（聊天）

```json
{
  "event": "im",
  "steamID": "76561199558480354",
  "fackname": "Ac",
  "steamname": "Ac",
  "date": "2026.11.20-23.46.47",
  "data": { "channel": "1", "message": "hi" }
}
```
- `date` 格式与游戏日志一致：`YYYY.MM.DD-HH.MM.SS`
- `channel` 即 `EChatType`：0/Default、1/Local、2/Global、3/Squad、4/Admin、5/CommandsOnly、6/ServerMessage、7/Error

### 16.3 实现方式（实时钩子，非读日志文件）

**钩点**：`Chat_Server_BroadcastChatMessage` 的原生实现
- RVA `0x28F6070`，首 5 字节 `48 89 5C 24 10`（`mov [rsp+0x10], rbx`）
- 补丁：`E9 rel32` → 桩（桩与跳板必须在 ±2GB 内，`AllocExecNear` 保证）
- 桩逻辑：保存 `rcx`(对象) / `rdx`(FFrame)，调用 `CaptureChat`，再执行原始 5 字节并跳回 `target+5`

**参数读取**（静态确认）
- `FFrame` 的 `Locals` 在 `+0x28`
- `Locals+0x00` = `Message`（FString：`+0 ptr`、`+8 Num 含结尾 NUL`）
- `Locals+0x10` = `Channel`（uint8）
- 原实现随后调用 `vtable+0x7F8` 的虚函数做实际广播

**投递**
- 事件入 `std::deque`（上限 2000，超出计 `dropped`）
- 工作线程 `CbWorker` 用 **WinHTTP** POST（失败重试一次）
- 统计：`sent` / `fail` / `dropped`，用 `python scumctl.py cbstate` 查看

### 16.4 控制命令

```
python scumctl.py cbstate          # enable/url/queued/sent/fail/dropped/chatHooked
python scumctl.py cbtest "hello"   # 投递一条合成事件（验证 HTTP 通路）
python scumctl.py cbreload         # 重新读配置 + 补挂钩子
```

### 16.5 已验证 / 待解决

**已验证**
- 钩子安装：`[cb] chat hook installed: target=00007FF6CFF46070 stub=... tramp=...`
- 聊天消息实时捕获：`message` 与 `channel` 正确（注入测试 `ascii-hook-test` 命中）
- HTTP 投递：`sent` 计数递增，接收端收到完整 JSON

**待解决（下一步第一件事）**
- 钩子内的 `steamID / steamname / fackname` 仍为空
  - 外部读取已验证正确：`通道+0xA0 → 控制器`，`控制器+0x6C8 = SteamID(17位)`、
    `+0x6E0 = 玩家名`、`+0x740 = 假名`
  - 钩子触发瞬间按 `ctx+0xA0`、`ctx+0x20` 及 `ctx` 前 0x200 字节扫描（最多 40 个候选）
    仍未取到；已加诊断 `[cb] dbg ctx=... nc=... c0=... q0=...`（未完成验证就收工）
  - 建议下一步：先看 `[cb] dbg` 里 `c0/q0` 是否指向控制器；若 `ctx` 在 RPC 期间不是
    `PlayerRpcChannel` 实例，改为从 `ctx` 的 Outer/owner 链或 GameMode→PlayerArray 取 SteamID
- 注入路径发送的中文消息出现编码错乱（外部客户端 → 控制协议），真实客户端聊天待复测
- HTTPS 回调未实现（只支持 `http://`）

### 16.6 游戏自带日志（参考，非实时）

目录 `Saved\\SaveFiles\\Logs`，**UTF-16LE**，按类型+时间分文件：`<type>_<YYYYMMDDHHMMSS>.log`
类型全集：`login`、`admin`、`chat`、`event_kill`、`kill`、`violations`、`economy`、`gameplay`、
`famepoints`、`loot`、`raid_protection`、`chest_ownership`、`quests`、`vehicle_destruction`、
`server_notifications`、`armor_absorption`、`sentry`、`base_building_destruction`、
`network_objects`、`nosteam`

聊天行格式：
```
2026.11.20-14.17.23:  '76561199558480354:Ac(1)'  'Local:  hi'
```
首行固定为 `Game version: 1.3.6.2.179673`。
"""
with open(README, "a", encoding="utf-8") as f:
    f.write(section)
print("ok")
