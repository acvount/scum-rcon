# scum-rcon

SCUM Windows 专用服务器的本机控制工具。插件加载到服务端进程后，在 `127.0.0.1:17880` 提供控制接口，Python 客户端可发送聊天、公告和管理员命令。

这是基于引擎反射与进程内插件的控制工具，不是 SCUM 官方 RCON 协议实现。管理员命令借用在线玩家的 RPC 通道执行，需要有在线玩家及相应管理员权限；客户端脚本默认选择最新创建的非模板通道，多人在线时不保证选中指定玩家。

## 环境要求

- Windows x64，已安装且可以正常运行的 SCUM 专用服务器。
- Python 3.10 或更高版本。下面的主要客户端只使用 Python 标准库，无需 `pip install`。
- 从源码编译需要 Visual Studio 2022 Build Tools、C++ x64 工具链、Windows SDK，以及 `cl`、`ml64`、`link`。
- 插件使用版本相关的引擎布局、偏移和虚表槽位。原资料记录的适配时间为 2026-11-20，不代表兼容之后的所有服务端版本。

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
| `--chattype 0` | 指定 ChatType 枚举值，默认 `0` |
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

## 4. 备用加载方式

如果不采用启动代理，可对已运行的服务端使用注入器。以具备目标进程访问权限的身份执行，DLL 必须使用绝对路径：

```bat
D:\scum-rcon\scum-harness\injector\scum_inject.exe SCUMServer.exe D:\scum-rcon\scum-harness\plugin\scum_harness.dll
```

第一个参数也可使用 PID。代理加载与注入选择一种即可，避免重复加载。注入后同样用 `ping`、`stat` 检查。

## 5. 故障排查

| 现象 | 检查方式 |
| --- | --- |
| 连接被拒绝或超时 | 确认服务端运行、DLL 位于正确可执行文件目录、日志出现 `control server listening`；客户端必须在服务器本机运行 |
| `stat` 尚未就绪 | 等待地图和对象表初始化，检查 `scum_harness.log` 中的初始化失败或重试信息 |
| `no live PlayerRpcChannel` | 让玩家进入服务器；管理员命令需要在线玩家通道 |
| 命令被拒绝或无效果 | 检查所选通道玩家的管理员权限、命令参数，以及服务端日志；多人在线时脚本默认选最新通道 |
| 找不到 `BroadcastChatLine` | 等待地图加载或让真实客户端连接以加载所需类，再重试；检查是否为版本不兼容 |
| 加载类失败，但聊天函数存在 | 脚本会继续尝试发送，以最终调用结果及游戏内显示为准 |
| `ex` 非零或升级后崩溃 | 停用插件并核对版本适配；不要沿用旧构建的地址、偏移或虚表槽位 |
| 编译找不到 `cl` / `ml64` | 确认安装 C++ x64 工具链，并修正 `build_all.bat` 中的 MSVC 环境路径 |
| 中文显示异常 | 检查终端编码及游戏内结果；命令和控制协议使用 UTF-8 |

升级或卸载插件时先停服，再替换或移走插件文件。若曾备份原有自定义 DLL，应恢复备份。

## 6. 文件说明

```text
scum-rcon/
├── README.md                  使用说明
├── scum-harness/
│   ├── build_all.bat          完整构建入口
│   ├── plugin/                C++ 插件、汇编、导出定义及已有构建产物
│   ├── injector/              注入器源码及已有构建产物
│   └── client/                Python 控制客户端与探测工具
├── scripts/scum_status.py     旧安装环境巡检脚本
├── Find-SCUM-Server.ps1        查找服务端的辅助脚本
├── 清理D盘_安全项.ps1          原环境磁盘清理脚本
└── .re/                       逆向研究脚本及数据，日常使用不需要
```

日常使用只需完整构建入口、部署 DLL 和三个主要客户端：`scumctl.py`、`scum_chat.py`、`scum_admin.py`。

其余探测、清理和研究脚本保留原样，可能含原机器路径或旧版本假设，不属于安装步骤。特别是 `scripts/scum_status.py` 仍按旧的 `SCUMServer-Win64-Shipping.exe` 文件名检查，不能用它的结果代替当前服务端的实际启动验证。
