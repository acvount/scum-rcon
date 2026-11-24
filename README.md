# scum-rcon

SCUM Windows 专用服务器的本机控制工具。插件加载到服务端进程后，在 `127.0.0.1:17880` 提供行协议控制接口，Python 客户端可发送聊天、公告和管理员命令；插件同时把聊天、登录和游戏日志事件实时回调到本机 HTTP 端点。

这是基于引擎反射与进程内插件的工具，不是 SCUM 官方 RCON 协议实现：

- 聊天、公告直接调用服务端对象的通知/广播函数，**不需要玩家在线**；
- 管理员命令借用在线玩家的 `PlayerRpcChannel` 执行，需要至少一名在线玩家提供通道，但权限校验对本地工具发起的调用直接放行（不依赖 `AdminUsers.ini`）。

## 环境要求

- Windows x64，已安装且可正常运行的 SCUM 专用服务器。
- Python 3.10 或更高版本。客户端只用标准库，无需 `pip install`。
- 从源码编译需要 Visual Studio 2022 Build Tools、C++ x64 工具链、Windows SDK，以及 `cl`、`ml64`、`link`。
- 插件使用版本相关的引擎布局、偏移（`0x28F6070` 聊天钩子、`0x1F8D8C0` 管理员判定）和虚表槽位。适配记录时间为 2026-11-21，不保证兼容之后的服务端版本。

以下示例假设仓库在 `D:\scum-rcon`、服务端在 `D:\SCUM_Server\server\SCUM\Binaries\Win64`，请替换为实际路径。

## 1. 获取与构建

```bat
git clone git@github.com:acvount/scum-rcon.git D:\scum-rcon
cd /d D:\scum-rcon
scum-harness\build_all.bat
```

`build_all.bat` 从以下位置加载 MSVC 环境，路径不同请先修改脚本：

```text
C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat
```

脚本依次编译汇编钩子、注入型插件、代理 DLL 和注入器，编译参数为 `/std:c++17 /EHa /O2 /MT /utf-8`。成功时依次输出：

```text
PLUGIN_BUILD_OK
PROXY_BUILD_OK
INJECTOR_BUILD_OK
```

| 产物 | 用途 |
| --- | --- |
| `scum-harness\plugin\dwmapi.dll` | 代理插件，随服务端启动加载，推荐 |
| `scum-harness\plugin\scum_harness.dll` | 注入型插件，备用 |
| `scum-harness\injector\scum_inject.exe` | 备用注入器 |

`plugin\build.bat` 是旧入口，只编译注入型插件，不要用它代替 `build_all.bat`。仓库内附带的 DLL/EXE 是既有构建产物，建议按当前源码与目标版本重新构建。

## 2. 部署插件

先停服。若目标目录已有自定义 `dwmapi.dll`，先备份并确认用途。

```bat
set "SCUM_BIN=D:\SCUM_Server\server\SCUM\Binaries\Win64"
copy "D:\scum-rcon\scum-harness\plugin\dwmapi.dll" "%SCUM_BIN%\dwmapi.dll"
copy "%SystemRoot%\System32\dwmapi.dll" "%SCUM_BIN%\dwmapi_orig.dll"
```

```text
SCUM\Binaries\Win64\
├── SCUMServer.exe
├── dwmapi.dll        代理插件（本工具）
└── dwmapi_orig.dll   系统 DLL 的改名副本，用于转发原有导出
```

代理按名字 `dwmapi_orig.dll` 加载被代理的系统库；找不到时回退到 `%SystemRoot%\System32\dwmapi.dll`，但同目录留一份 `dwmapi_orig.dll` 更稳妥。`dwmapi_orig.dll` 不是构建产物。

用原有方式启动服务端，等待地图与插件初始化。插件初始化完成后才开始工作，日志写在服务端 exe 同目录的 `scum_harness.log`，应出现：

```text
[main] control server listening on 127.0.0.1:17880
```

在服务器本机确认连通：

```bat
cd /d D:\scum-rcon
python scum-harness\client\scumctl.py ping
python scum-harness\client\scumctl.py stat
```

`ping` 返回 `{"ok":true,"pong":true}`；`stat` 返回 `ready`、`objects`、`module`、`names`、`gobjects`、`pe_index`，`ready:false` 表示对象表尚未就绪。接口只监听回环地址、无认证，客户端必须在服务器本机运行。

## 3. 常用操作

命令都在仓库根目录执行。含空格或中文的参数用双引号包住，参数里避免再出现双引号和换行。

### 3.1 聊天广播（无需玩家在线）

```bat
python scum-harness\client\scum_chat.py "大家好，欢迎进入服务器"
```

流程：`tickprobe` 定位游戏线程 → `gtload` 加载 `BP_ConZPlayerController` → 全函数扫描定位 `BroadcastChatLine` → 取带真实世界（outer 为 `PersistentLevel`）的 `BP_ConZGameMode_C` 实例作 WorldContextObject → 在游戏线程 `gtcallpe` 调用 `BroadcastChatLine(WorldContextObject, Text, ChatType)`。全程走服务端对象，零玩家在线也能发送。

| 参数 | 含义 |
| --- | --- |
| `--chattype N` | ChatType 枚举，默认 `0`；`2` 为 Global |
| `--port N` | 控制接口端口，默认 `17880` |
| `--ctx 0x地址` | 手动指定 WorldContextObject；只接受 `0x` 开头的地址，缺省自动查找 GameMode 实例 |

`--reload` 参数被解析但当前实现不使用，每次运行都会尝试加载类。脚本输出 `RESULT: SUCCESS` 表示引擎调用已触发且 `ex == 0`，失败时退出码 1；消息是否真的显示，需要在线客户端确认。

### 3.2 公告 / 通知（无需玩家在线）

```bat
python scum-harness\client\scumctl.py announce "服务器将在十分钟后重启"
```

控制命令 `announce` 调用服务端 ChatManager 上的通知函数（依次尝试 `Multicast_DisplayNotification`、`Multicast_ShowEventNotification`、`NetMulticast_RequestNotification`、`Client_ShowNotification`），按参数名 `Title`/`NotificationText`/`Text` 与 `Body`/`Message`/`Description` 匹配，不经过玩家 RPC 通道，零玩家在线也能发送。

注意：`scum_admin.py "Announce ..."` 走的是下面的管理员命令通道，需要在线玩家；两者不是同一条路径。

### 3.3 管理员命令（需要在线玩家提供通道）

至少一名玩家在线，用于提供 `PlayerRpcChannel`：

```bat
python scum-harness\client\scum_admin.py "Announce 服务器将在十分钟后重启"
python scum-harness\client\scum_admin.py "ListPlayers"
python scum-harness\client\scum_admin.py "SpawnItem Apple 1"
python scum-harness\client\scum_admin.py "Teleport -660000 -270000 12000 PlayerName"
python scum-harness\client\scum_admin.py --list
```

实现方式是调用玩家通道上的 `Chat_Server_ProcessAdminCommand` 原生 RPC，等价于该玩家在聊天框输入 `#命令`：

- 命令可带或不带开头的 `#`，脚本会先剥掉（服务端期望不带）。
- `Teleport` 参数顺序为 `X Y Z [玩家]`，坐标在前；省略玩家时作用于所选通道的玩家。
- `SpawnItem` 仍受服务端物品与命令自身规则约束，不是所有物品都可生成。
- `--list` 以 `findclass AdminCommand` 列出当前对象表里的管理员命令类，清单取决于服务端版本与已加载对象。
- 返回 `{"ok":true,"fired":true,"ex":0,"fn":...,"channel":"0x...","controller":"0x..."}` 只代表引擎调用完成；命令是否获准并生效，以服务端日志的 `Command:` 行或游戏内结果为准。

相对传送：以通道玩家当前位置为基准，X/Y 加偏移、Z 加 120（引擎单位厘米），可在末尾附加目标玩家名（基准仍是通道玩家）：

```bat
python scum-harness\client\scum_admin.py --tp 5000 5000
```

**权限**：插件在管理员判定函数（`RVA 0x1F8D8C0`，返回 1 表示是管理员）入口前加了过滤器，本地工具发起的调用（`gtcall`/`gtcallpe` 期间 `g_injectDepth > 0`）直接返回 1，不再比对 SteamID 或 `AdminUsers.ini`；游戏内玩家手打的 `#` 命令仍走原始校验。因此被借用的通道不需要属于管理员账号。

**通道选择**：脚本遍历对象表里的 `PlayerRpcChannel`，排除 `Default__` 前缀与 `/Script/` 模板对象，再打分——owner 类名含 `PlayerController` 得 2 分、能在通道里定位到带坐标的角色（pawn）得 5 分，取最高分，平手取对象索引最大者。玩家重连会留下失效通道，只按索引取最大容易选到过期对象（症状：`ex=0` 但服务端日志没有 `Command:` 行）。

失败时脚本直接返回错误文本：`Chat_Server_ProcessAdminCommand not found (class not loaded?)` 表示函数不在对象表；`no live PlayerRpcChannel - player offline?` 表示没有可用通道。

### 3.4 可选：指定 SteamID 的管理员钩子

本地工具的命令已按调用来源放行，不需要这项配置。这个钩子用于让某个账号**在游戏内**输入 `#` 命令时也被判定为管理员，适合不改 `AdminUsers.ini` 的场景。

在服务端 exe 同目录创建 `scum_harness_admin.txt`，内容仅为 SteamID，不带 BOM，然后重启服务端（读取时会自动去掉行尾 `\r`/`\n`/空格）：

```powershell
[System.IO.File]::WriteAllText('D:\SCUM_Server\server\SCUM\Binaries\Win64\scum_harness_admin.txt', '替换为目标SteamID', [System.Text.Encoding]::ASCII)
```

启动后日志应出现：

```text
[admhook] installed: target=... stub=... tramp=...
[admhook] auto-installed for <steamid>
```

检查状态：

```bat
python scum-harness\client\scumctl.py admstate
```

返回 `hooked`、`target`、`stub`。钩子靠 `mov [rsp+0x10], rbx`（`48 89 5C 24 10`）识别目标函数，序言不匹配时日志为 `[admhook] auto-install FAILED (prologue mismatch?)`，此时按版本重新适配偏移。

停用：先停服，移走 `scum_harness_admin.txt`，再启动——只删文件不会卸载当前进程里已装好的钩子。已有管理员配置仍可能通过原有权限路径获准，这个钩子不等于撤销其它管理员权限。

## 4. 实时事件回调（可选）

插件把聊天、登录/登出和游戏日志事件逐条 POST 到本机 HTTP 端点，供面板、机器人、群通知使用。不配置时回调关闭，其余功能不受影响。

### 4.1 配置

在服务端 exe 同目录创建 `YG_CONFIG.json`：

```json
{
  "enable": true,
  "url": "http://127.0.0.1:8080/scum/event"
}
```

- `enable`：控制实时聊天钩子。为 `false` 时钩子照常安装，但采集入口直接返回，不产生钩子聊天事件。
- `url`：投递地址，必须以 `http://` 开头，格式 `http://host[:port]/path`，缺省端口 80。**只要 `url` 非空，日志事件（`login`/`log`/日志来源的 `im`）与 `cbtest` 合成事件就会投递，与 `enable` 无关**；`url` 为空时事件出队后直接计入 `fail`。
- 配置文件按普通文件一次读入，缓冲区 4096 字节，保持精简。
- 改完执行 `scumctl.py cbreload` 即时生效：重读配置，并在未挂钩子时补挂聊天钩子。

投递使用 WinHTTP POST，`Content-Type: application/json; charset=utf-8`、`Connection: close`，HTTP 2xx 视为成功，失败重试一次，仍失败计入 `fail`。

### 4.2 事件格式

每条形如：

```json
{"event":"...","steamID":"...","fackname":"...","steamname":"...","date":"YYYY.MM.DD-HH.MM.SS","data":{...}}
```

`date` 与游戏日志时间戳同格式。下面按 `event` 说明。

**聊天 `im`（实时钩子）**

```json
{"event":"im","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-10.29.11",
 "data":{"channel":"2","message":"你好"}}
```

- 来自 `Chat_Server_BroadcastChatMessage` 原生实现上的钩子，**没有 `source` 字段**（与日志来源区分）。
- `channel` 是字符串形式的 `EChatType`：`0` Default、`1` Local、`2` Global、`3` Squad、`4` Admin、`5` CommandsOnly、`6` ServerMessage、`7` Error。
- 身份字段从通道对象推导：`ctx+0xA0`、`ctx+0x20` 以及 `ctx` 前 `0x200` 字节里最多 40 个候选中，找 `+0x6C8` 为 17 位数字（SteamID）的对象，再读 `+0x6E0` 玩家名、`+0x740` 假名。取不到时这三个字段为空字符串。前几次调用会在日志写 `[cb] dbg ctx=... nc=...` 便于定位。

**聊天 `im`（日志来源）**

```json
{"event":"im","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-10.29.11",
 "data":{"channel":"2","message":"你好","source":"log"}}
```

来自 `chat_*.log`，多一个 `"source":"log"`。频道名 `Local`/`Global`/`Squad`/`Admin` 会映射成 1/2/3/4；其它频道保留原始名（例如 `"channel":"CommandsOnly"`）。

**登录/登出 `login`**

```json
{"event":"login","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-02.55.51",
 "data":{"action":"login","ip":"192.168.1.112",
         "position":"X=467147.000,Y=-260984.000,Z=14534.000","source":"log"}}
```

来自 `login_*.log`（`admin_*.log` 也先尝试这条路）；`action` 为 `login` 或 `logout`，`position` 里的空格已替换成逗号。

**其它日志 `log`**

```json
{"event":"log","type":"loot","steamID":"","fackname":"","steamname":"",
 "date":"2026.11.21-02.51.55",
 "data":{"text":"...","file":"loot_20261121025155.log"}}
```

`type` 取文件名前缀。常见值：`admin`、`chat`、`login`、`loot`、`kill`、`event_kill`、`gameplay`、`economy`、`famepoints`、`quests`、`raid_protection`、`chest_ownership`、`vehicle_destruction`、`server_notifications`、`base_building_destruction`、`violations`、`sentry`、`network_objects`、`armor_absorption`、`nosteam`。

### 4.3 数据来源与实现细节

- **实时钩子**：钩 `Chat_Server_BroadcastChatMessage` 原生实现（`RVA 0x28F6070`，序言 `48 89 5C 24 10`）。桩与跳板用 `E9 rel32` 跳转，必须落在目标 ±2GB 内。参数从 `FFrame+0x28 → Locals` 读取：`+0x00` Message（FString）、`+0x08` 长度、`+0x10` Channel（uint8）。序言不匹配时日志写 `[cb] chat hook prologue mismatch`，不装钩子。
- **日志泵**：目录为服务端 exe 的 `..\..\Saved\SaveFiles\Logs`，文件名为 `<type>_<YYYYMMDDHHMMSS>.log`，编码 UTF-16LE。启动时先建立基线（只记录当前文件大小，不回放历史），之后每 250ms 扫描一次，单次最多读 256KB。
- **偏移对齐**：读取偏移必须偶数对齐，否则 UTF-16 半字节错位会整段乱码。
- **末行提交**：只有真正产出了完整行才推进偏移；没有换行的末行要等文件大小连续两个周期不变才提交，否则会永久丢失。
- **编码修复**：文本里出现 CJK 时按 GBK 回滚成 UTF-8（游戏把 UTF-8 字节当 GBK 解释），失败则保留原文。
- **队列**：事件入 `std::deque`，长度超过 2000 条时丢弃并计入 `dropped`。
- **体积**：单条聊天消息长度上限 2000 字符，超长不采集。

### 4.4 控制命令

```bat
python scum-harness\client\scumctl.py cbstate
python scum-harness\client\scumctl.py cbreload
python scum-harness\client\scumctl.py cbtest "hello"
python scum-harness\client\scumctl.py cbloginfo login
```

| 命令 | 返回 |
| --- | --- |
| `cbstate` | `enable`、`url`、`queued`、`sent`、`fail`、`dropped`、`chatHooked`、`logEvents` |
| `cbreload` | 重读 `YG_CONFIG.json`、补挂聊天钩子，返回同上状态 |
| `cbtest "文本"` | 投递一条合成 `im` 事件，返回当前 `queued` |
| `cbloginfo <前缀>` | 列出 `<前缀>_*.log` 的 `name`/`type`/`size`/`offset`/`lag`（无参数则列全部，最多 60 个） |

`fail` 持续增长说明端点不可达或返回非 2xx；`dropped` 增长说明积压超过 2000 条。

### 4.5 本地接收端

```bat
python scum-harness\client\scum_cb_recv.py
python scum-harness\client\scum_cb_recv.py --host 127.0.0.1 --port 8080 --out events.jsonl
```

多线程 HTTP 服务，每条事件打印到终端并追加一行到 `--out`（默认 `events.jsonl`，UTF-8）。终端需 `chcp 65001` 与 `PYTHONIOENCODING=utf-8` 才能正确显示中文，落盘文件本身是 UTF-8。

## 5. 备用加载方式

不用启动代理时，可对已运行的服务端注入。以具备目标进程访问权限的身份执行，DLL 用绝对路径：

```bat
D:\scum-rcon\scum-harness\injector\scum_inject.exe SCUMServer.exe D:\scum-rcon\scum-harness\plugin\scum_harness.dll
```

第一个参数可以是进程名或 PID。代理加载与注入二选一，不要重复加载。注入后同样用 `ping`、`stat` 验证。

## 6. 控制接口命令速查

接口是行协议：一次连接发一行命令（参数用空格分隔，含空格的参数加双引号），返回一行 JSON。`scumctl.py` 只是把参数原样拼成这一行，所以 `python scumctl.py cbstate` 等价于发送 `cbstate`。

| 命令 | 作用 |
| --- | --- |
| `ping` | 连通性检查 |
| `stat` | 模块基址、对象表/名字池地址、对象数、`ready` |
| `announce <文本>` | 服务端公告/通知，无需玩家 |
| `chat <发送者> <SteamID> <文本>` | 直接走聊天管理器广播 |
| `classes [N]` | 按类名统计对象数量 |
| `funcs [关键字]` | 搜索 UFunction 名 |
| `desc <函数名>` | 列出参数名/偏移/大小 |
| `gtcallpe <函数名或0x地址> [ctx] [参数...]` | 在游戏线程经 `ProcessEvent` 调用 |
| `cbstate` / `cbreload` / `cbtest` / `cbloginfo` | 见 4.4 |
| `admstate` | 管理员钩子状态 |

更多诊断命令（`gtload`、`tickprobe`、`dumpfuncsraw`、`findinst`、`writemem` 等）保留在源码里，属于逆向调试用途，日常不需要。

## 7. 故障排查

| 现象 | 检查方式 |
| --- | --- |
| 连接被拒绝或超时 | 服务端是否运行、DLL 是否在 exe 同目录、日志是否有 `control server listening`；客户端必须在服务器本机 |
| `stat` 的 `ready:false` | 等地图与对象表初始化；看 `scum_harness.log` 里 `[main] init retry` |
| 公告没有反应 | `announce` 返回 `ok:false` 时看 `error`（通常是 `manager not found` 或函数名不匹配） |
| 聊天脚本报 `BroadcastChatLine 不在对象表` | 类未加载或被 GC：让真实客户端连一次，或检查版本兼容 |
| `no live PlayerRpcChannel - player offline?` | 管理员命令需要在线玩家通道；公告与聊天广播不需要 |
| `Chat_Server_ProcessAdminCommand not found` | 函数不在对象表，通常是对应类未加载 |
| 管理员命令 `ex=0` 但没生效 | 看服务端日志有没有 `Command:` 行；没有说明选到了过期通道，重启客户端脚本重选 |
| 命令被拒绝 | 检查命令参数与服务端规则；本地调用已跳过管理员名单校验，游戏内手打命令仍受 `AdminUsers.ini` 约束 |
| `ex` 非零或升级后崩溃 | 停用插件并重新适配偏移；不要沿用旧构建的地址与虚表槽位 |
| 编译找不到 `cl` / `ml64` | 装 C++ x64 工具链并修正 `build_all.bat` 里的 vcvars 路径 |
| 中文显示异常 | 终端编码与游戏内结果一起看；控制协议与事件均为 UTF-8 |
| `cbstate` 里 `chatHooked:false` | 序言不匹配或版本不符，看日志 `[cb] chat hook prologue mismatch`；执行 `cbreload` 重试 |
| 收不到任何事件 | 核对 `YG_CONFIG.json` 的 `enable`/`url`、接收端是否在监听、`sent` 是否增长 |
| 只有 `login`/`log` 没有 `im` | 聊天钩子依赖版本偏移；日志链路仍会产出 `source:log` 的聊天事件 |
| `cbloginfo` 里 `lag` 一直增长 | 日志泵读取落后：检查是否有大量写入、单次 256KB 上限是否长期打满 |

升级或卸载：先停服，再替换或移走插件文件；曾备份过自定义 DLL 的应恢复备份。

## 8. 文件说明

```text
scum-rcon/
├── README.md                  使用说明
├── scum-harness/
│   ├── build_all.bat          完整构建入口
│   ├── plugin/                C++ 插件、汇编钩子、代理 DLL 及已有构建产物
│   ├── injector/              注入器源码及已有构建产物
│   └── client/                Python 客户端：scumctl / scum_chat / scum_admin / scum_cb_recv
├── scripts/scum_status.py     旧安装环境巡检脚本
├── Find-SCUM-Server.ps1        查找服务端的辅助脚本
└── .re/                       逆向研究脚本与数据，日常使用不需要
```

日常只需 `build_all.bat`、部署的 DLL 和四个客户端脚本。`YG_CONFIG.json`、`scum_harness_admin.txt`、`scum_harness.log` 均在服务端目录按需生成，不随仓库分发。

`client/` 下的 `probe_*.py`、`send_announce.py`、`verify_utf8.py` 是开发期验证脚本，可能含原机器路径或旧版本假设，不属于安装与日常使用步骤。`scripts/scum_status.py` 仍按旧的 `SCUMServer-Win64-Shipping.exe` 文件名检查，其结果不能替代对当前服务端的实际启动验证。
