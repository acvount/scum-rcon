# scum-rcon

SCUM Windows 专用服务器的本机控制工具。插件加载到服务端进程后，在 `127.0.0.1:17880` 提供控制接口，Python 客户端可发送聊天、公告和管理员命令；插件同时可以把聊天、登录和游戏日志事件实时回调到本机 HTTP 端点。

这是基于引擎反射与进程内插件的控制工具，不是 SCUM 官方 RCON 协议实现。管理员命令借用在线玩家的 RPC 通道执行，需要有在线玩家及相应管理员权限；客户端脚本会优先选择 owner 带角色的通道，多人在线时不保证一定选中指定玩家。

## 环境要求

- Windows x64，已安装且可以正常运行的 SCUM 专用服务器。
- Python 3.10 或更高版本。下面的客户端只使用 Python 标准库，无需 `pip install`。
- 从源码编译需要 Visual Studio 2022 Build Tools、C++ x64 工具链、Windows SDK，以及 `cl`、`ml64`、`link`。
- 插件使用版本相关的引擎布局、偏移和虚表槽位。原资料记录的适配时间为 2026-11-21，不代表兼容之后的所有服务端版本。

下面以仓库位于 `D:\scum-rcon`、服务端可执行文件位于 `D:\SCUM_Server\server\SCUM\Binaries\Win64\SCUMServer.exe` 为例，请替换成实际路径。

## 1. 获取与构建

```bat
git clone git@github.com:acvount/scum-rcon.git D:\scum-rcon
cd /d D:\scum-rcon
scum-harness\build_all.bat
```

`build_all.bat` 默认从以下位置加载 MSVC 环境：

```text
C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat
```

若安装位置不同，先修改脚本中的路径。请使用 `build_all.bat`，它会一起构建插件、代理 DLL、汇编钩子和注入器；`plugin\build.bat` 是旧构建入口，不作为完整构建方式。

构建完成应出现 `PLUGIN_BUILD_OK`、`PROXY_BUILD_OK`、`INJECTOR_BUILD_OK`，并生成：

| 文件 | 用途 |
| --- | --- |
| `scum-harness\plugin\dwmapi.dll` | 随服务端启动加载的代理插件，推荐部署方式 |
| `scum-harness\plugin\scum_harness.dll` | 向已启动进程加载的插件，备用方式 |
| `scum-harness\injector\scum_inject.exe` | 备用注入器 |

目录内附带的 DLL/EXE 属于已有构建产物，建议使用与当前源码和目标环境匹配的重新构建结果。

## 2. 部署插件

先停止 SCUM 服务端。若服务端目录已有自定义 `dwmapi.dll`，先备份并确认用途，避免直接覆盖。

在 Windows 命令提示符中执行：

```bat
set "SCUM_BIN=D:\SCUM_Server\server\SCUM\Binaries\Win64"
copy "D:\scum-rcon\scum-harness\plugin\dwmapi.dll" "%SCUM_BIN%\dwmapi.dll"
copy "%SystemRoot%\System32\dwmapi.dll" "%SCUM_BIN%\dwmapi_orig.dll"
```

最终目录如下：

```text
SCUM\Binaries\Win64\
├── SCUMServer.exe
├── dwmapi.dll
└── dwmapi_orig.dll
```

`dwmapi_orig.dll` 是目标 Windows 系统 DLL 的改名副本，用来转发原有系统调用。它不是构建脚本生成的文件。

使用原有启动方式启动服务端，等待地图和插件初始化完成。仓库不提供完整服务端安装包，也不包含 `start_server.bat`；可执行文件名以实际安装为准。

在服务端所在机器检查连接：

```bat
cd /d D:\scum-rcon
python scum-harness\client\scumctl.py ping
python scum-harness\client\scumctl.py stat
```

`ping` 返回 `ok: true` 代表控制接口可连接；`stat` 用来检查对象表和名字池等初始化信息。日志位于插件目录下的 `scum_harness.log`。

接口只监听本机回环地址，没有独立认证。Python 客户端应在服务器本机运行。

## 3. 常用操作

以下命令都在仓库根目录执行。包含空格或中文的消息用双引号包住，消息内避免再使用双引号和换行。

### 聊天广播

```bat
python scum-harness\client\scum_chat.py "大家好，欢迎进入服务器"
```

脚本会尝试加载所需类、查找聊天函数和真实 GameMode 实例，再通过游戏线程的 `ProcessEvent` 路径发送消息。

可选参数：

| 参数 | 含义 |
| --- | --- |
| `--chattype 0` | 指定 ChatType 枚举值，默认 `0`；`2` 为 Global |
| `--port 17880` | 指定客户端连接端口；不会修改插件的监听端口 |
| `--ctx 0x地址` | 手动指定 WorldContextObject，通常不需要 |

`--reload` 虽然在脚本中接受，但当前实现没有根据它切换行为：每次运行都会尝试加载类，因此无需额外传入。

`RESULT: SUCCESS` 表示插件报告调用已触发且未返回异常；是否实际显示需在在线游戏客户端确认，零玩家时无法验证消息送达。

### 公告及管理员命令

先让具有管理员权限的玩家上线，并确认脚本选中的通道属于有权限的玩家，然后执行：

```bat
python scum-harness\client\scum_admin.py "Announce 服务器将在十分钟后重启"
python scum-harness\client\scum_admin.py "ListPlayers"
python scum-harness\client\scum_admin.py "SpawnItem Apple 1"
python scum-harness\client\scum_admin.py "Teleport -660000 -270000 12000 PlayerName"
python scum-harness\client\scum_admin.py --list
```

- 命令可带或不带开头的 `#`，脚本会自动去掉。
- `Teleport` 的参数顺序是 `X Y Z [玩家]`，坐标在前，玩家在后；省略玩家时作用于所选通道的玩家。
- `SpawnItem` 受服务端物品与权限规则约束，并非所有物品都允许生成。
- `--list` 从当前对象表列出管理员命令类，实际清单取决于服务端版本和已加载对象。
- 返回 `fired: true`、`ex: 0` 只说明引擎调用完成；业务命令是否获准并生效，仍需查看服务端日志或游戏内结果。

通道选择：脚本遍历对象表里的 `PlayerRpcChannel`，优先挑选 owner 是 `PlayerController` 且能定位到角色（pawn）的通道，其次才取对象索引最大的通道。多人在线时可以先用 `ListPlayers` 确认通道对应的玩家。

相对传送示例：

```bat
python scum-harness\client\scum_admin.py --tp 5000 5000
```

脚本以所选通道玩家的当前位置为基准，在 X、Y 上增加指定偏移，在 Z 上增加 120；单位为引擎坐标厘米。可在末尾附加目标玩家名，但基准仍是所选通道玩家的位置。

### 可选：指定 SteamID 的管理员钩子

插件还提供指定 SteamID 的进程内管理员判定钩子。只使用服务端原有管理员配置时，无需开启此功能。

如需沿用原工具的指定 SteamID 模式，在插件目录创建 `scum_harness_admin.txt`，内容仅为目标 SteamID，不带 BOM，然后重启服务端。PowerShell 示例：

```powershell
[System.IO.File]::WriteAllText('D:\SCUM_Server\server\SCUM\Binaries\Win64\scum_harness_admin.txt', '替换为目标SteamID', [System.Text.Encoding]::ASCII)
```

检查安装结果：

```bat
python scum-harness\client\scumctl.py admstate
```

应检查 `hooked: true`、目标 ID，以及日志中的 `[admhook] installed`、`[admhook] auto-installed`。原资料中的独占验证使用空的 `Saved\Config\WindowsServer\AdminUsers.ini`；已有管理员配置仍可能通过原有权限路径获准，钩子不等于撤销所有其他管理员权限。此钩子同样依赖目标版本偏移。

停用自动安装时，先停服，再移走 `scum_harness_admin.txt`，然后重启；仅删除文件不会卸载当前进程已安装的钩子。

## 4. 实时事件回调（可选）

插件可把聊天、登录/登出和其它游戏日志事件实时 POST 到本机 HTTP 端点，供面板、机器人或群通知使用。不配置该文件时回调保持关闭，其余功能不受影响。

### 4.1 配置

在插件目录（与服务端 exe 同级）创建 `YG_CONFIG.json`：

```json
{
  "enable": true,
  "url": "http://127.0.0.1:8080/scum/event"
}
```

- `enable`：总开关。
- `url`：回调地址，当前只支持 `http://`。
- 修改配置后执行 `python scum-harness\client\scumctl.py cbreload` 即时生效，无需重启服务端。

### 4.2 事件格式

每次投递是一个独立 JSON 对象，按 `event` 字段区分类型。

**聊天 `im`**

```json
{"event":"im","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-10.29.11",
 "data":{"channel":"2","message":"你好","source":"log"}}
```

`channel` 为 `EChatType`：0/Default、1/Local、2/Global、3/Squad、4/Admin、5/CommandsOnly、6/ServerMessage、7/Error。`source` 区分来源：`hook`（聊天 RPC 实时钩子）或 `log`（聊天日志）。

**登录/登出 `login`**

```json
{"event":"login","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-02.55.51",
 "data":{"action":"login","ip":"192.168.1.112",
         "position":"X=467147.000,Y=-260984.000,Z=14534.000","source":"log"}}
```

`action` 为 `login` 或 `logout`。

**其它日志 `log`**

```json
{"event":"log","type":"loot","date":"2026.11.21-02.51.55",
 "data":{"text":"...","file":"loot_20261121025155.log"}}
```

`type` 取日志文件名前缀，常见值：`admin`、`chat`、`login`、`loot`、`kill`、`event_kill`、`gameplay`、`economy`、`famepoints`、`quests`、`raid_protection`、`chest_ownership`、`vehicle_destruction`、`server_notifications`、`base_building_destruction`、`violations`、`sentry`、`network_objects`、`armor_absorption`、`nosteam`。

### 4.3 数据来源与限制

- 聊天有两条链路：`Chat_Server_BroadcastChatMessage` 原生实现上的实时钩子（RVA 相关，随版本变化），以及 `Saved\SaveFiles\Logs\chat_*.log` 的增量读取。日志泵启动时先建立基线，只推送之后的新增行。
- 登录和其余事件只来自日志泵，周期约 250ms，属于近实时；单次最多读取 256KB，末行按“文件大小连续两个周期不变”提交。
- 游戏日志为 UTF-16LE，按类型分文件；中文文本存在双重编码，插件会尝试按 GBK→UTF-8 回滚，失败则保留原文。
- 事件队列上限 2000 条，超出计入 `dropped`；投递失败重试一次。
- 只支持明文 `http://`；回调端点需可由服务器本机访问。

### 4.4 控制命令

```bat
python scum-harness\client\scumctl.py cbstate
python scum-harness\client\scumctl.py cbreload
python scum-harness\client\scumctl.py cbtest "hello"
python scum-harness\client\scumctl.py cbloginfo login
```

| 命令 | 作用 |
| --- | --- |
| `cbstate` | 显示 enable / url / queued / sent / fail / dropped / logEvents / chatHooked |
| `cbreload` | 重新读取 `YG_CONFIG.json` 并补挂聊天钩子 |
| `cbtest "hello"` | 投递一条合成事件，用于验证 HTTP 通路 |
| `cbloginfo <type>` | 显示某类日志文件的大小、读取偏移和落后字节 |

### 4.5 本地接收端

仓库带一个最小接收端，用于验证回调是否打通：

```bat
python scum-harness\client\scum_cb_recv.py
python scum-harness\client\scum_cb_recv.py --port 8080 --out events.jsonl
```

它以多线程 HTTP 监听 `127.0.0.1:8080`，每条事件打印到终端并追加到 `--out` 指定文件（默认 `events.jsonl`）。终端需 `chcp 65001` 与 `PYTHONIOENCODING=utf-8`，否则中文显示为乱码（落盘文件本身是 UTF-8）。

## 5. 备用加载方式

如果不采用启动代理，可对已运行的服务端使用注入器。以具备目标进程访问权限的身份执行，DLL 必须使用绝对路径：

```bat
D:\scum-rcon\scum-harness\injector\scum_inject.exe SCUMServer.exe D:\scum-rcon\scum-harness\plugin\scum_harness.dll
```

第一个参数也可使用 PID。代理加载与注入选择一种即可，避免重复加载。注入后同样用 `ping`、`stat` 检查。

## 6. 故障排查

| 现象 | 检查方式 |
| --- | --- |
| 连接被拒绝或超时 | 确认服务端运行、DLL 位于正确可执行文件目录、日志出现 `control server listening`；客户端必须在服务器本机运行 |
| `stat` 尚未就绪 | 等待地图和对象表初始化，检查 `scum_harness.log` 中的初始化失败或重试信息 |
| `no live PlayerRpcChannel` | 让玩家进入服务器；管理员命令需要在线玩家通道 |
| 命令被拒绝或无效果 | 检查所选通道玩家的管理员权限、命令参数，以及服务端日志；多人在线时先 `ListPlayers` 确认通道 |
| 找不到 `BroadcastChatLine` | 等待地图加载或让真实客户端连接以加载所需类，再重试；检查是否为版本不兼容 |
| 加载类失败，但聊天函数存在 | 脚本会继续尝试发送，以最终调用结果及游戏内显示为准 |
| `ex` 非零或升级后崩溃 | 停用插件并核对版本适配；不要沿用旧构建的地址、偏移或虚表槽位 |
| 编译找不到 `cl` / `ml64` | 确认安装 C++ x64 工具链，并修正 `build_all.bat` 中的 MSVC 环境路径 |
| 中文显示异常 | 检查终端编码及游戏内结果；命令和控制协议使用 UTF-8 |
| `cbstate` 显示 `chatHooked:false` | 聊天钩子未挂上：确认服务端版本匹配、执行 `cbreload`，并查看日志中的 `[cb] chat hook installed` |
| 收不到任何事件 | 确认 `YG_CONFIG.json` 的 `enable` 与 `url`、接收端在监听、`sent` 计数是否增长；`fail` 增长说明端点不可达 |
| 只有 `login`/`log` 没有 `im` | 聊天钩子依赖版本偏移；日志链路仍会产出 `source:log` 的聊天事件 |
| 事件重复或串码 | 日志泵按文件增量读取，重启或回滚日志文件会重放；中文已做 GBK 回滚，仍有异常时以游戏内文本为准 |

升级或卸载插件时先停服，再替换或移走插件文件；若曾备份原有自定义 DLL，应恢复备份。

## 7. 文件说明

```text
scum-rcon/
├── README.md                  使用说明
├── scum-harness/
│   ├── build_all.bat          完整构建入口
│   ├── plugin/                C++ 插件、汇编、导出定义及已有构建产物
│   ├── injector/              注入器源码及已有构建产物
│   └── client/                Python 控制客户端与事件接收端
├── scripts/scum_status.py     旧安装环境巡检脚本
├── Find-SCUM-Server.ps1        查找服务端的辅助脚本
├── 清理D盘_安全项.ps1          原环境磁盘清理脚本
└── .re/                       逆向研究脚本及数据，日常使用不需要
```

日常使用只需完整构建入口、部署 DLL 和客户端脚本：`scumctl.py`（控制接口与回调命令）、`scum_chat.py`（聊天广播）、`scum_admin.py`（管理员命令）、`scum_cb_recv.py`（事件接收端）。

`YG_CONFIG.json`、`scum_harness_admin.txt`、`scum_harness.log` 均在服务端插件目录按需生成，不随仓库分发。

其余探测、清理和研究脚本保留原样，可能含原机器路径或旧版本假设，不属于安装步骤。特别是 `scripts/scum_status.py` 仍按旧的 `SCUMServer-Win64-Shipping.exe` 文件名检查，不能用它的结果代替当前服务端的实际启动验证。
