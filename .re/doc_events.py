# -*- coding: utf-8 -*-
README = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\README.md"
section = """

---

## 17. 事件回调系统（最终版，2026-11-21 实测通过）

### 17.1 配置文件

`D:\\SCUM_Server\\server\\SCUM\\Binaries\\Win64\\YG_CONFIG.json`
```json
{
  "enable": true,
  "url": "http://127.0.0.1:8080/scum/event"
}
```
- 改完执行 `python scumctl.py cbreload` 即时生效
- 仅支持 `http://`（HTTPS 未接）

### 17.2 事件类型

**① 聊天 `im`**（来源：聊天钩子 + 聊天日志两条路，`source` 字段区分）
```json
{"event":"im","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-10.29.11",
 "data":{"channel":"2","message":"你好","source":"log"}}
```
- `channel`：0/Default、1/Local、2/Global、3/Squad、4/Admin、5/CommandsOnly、6/ServerMessage、7/Error

**② 登录/登出 `login`**（结构化）
```json
{"event":"login","steamID":"76561199558480354","fackname":"Ac","steamname":"Ac",
 "date":"2026.11.21-02.55.51",
 "data":{"action":"login|logout","ip":"192.168.1.112",
         "position":"X=467147.000,Y=-7...","source":"log"}}
```

**③ 其它日志事件 `log`**（15+ 种类型）
```json
{"event":"log","type":"loot|gameplay|kill|economy|quests|violations|...",
 "date":"2026.11.21-02.51.55","data":{"text":"...","file":"gameplay_2026....log"}}
```

### 17.3 数据来源（两条独立链路）

**A. 实时钩子**（聊天 RPC）
- 钩 `Chat_Server_BroadcastChatMessage` 原生实现（RVA `0x28F6070`，首 5 字节 `48 89 5C 24 10`）
- 参数：`FFrame+0x28 = Locals` → `+0x00` Message(FString)、`+0x10` Channel(uint8)
- 身份：`ctx+0xA0` → 控制器 → `+0x6C8` SteamID、`+0x6E0` 玩家名、`+0x740` 假名
- 有 `[cb] dbg` 诊断行（前若干次调用）

**B. 日志泵**（近实时，250ms 周期）
- 目录：`Saved\\SaveFiles\\Logs`，UTF-16LE，按 `<type>_<YYYYMMDDHHMMSS>.log` 分文件
- 启动瞬间（`BootThread`）建立基线，只推送新增内容
- **关键坑（全部已修）**：
  1. 偏移必须**偶数对齐**（UTF-16 半字节偏移会导致整段乱码）
  2. 读完后**不能无条件推进偏移**，否则"无换行的末行"永久丢失
     → 只在真正提交行后推进；末行按"文件大小连续 2 周期不变"提交
  3. 聊天文本双重编码：游戏把 UTF-8 字节按 GBK 解释（`你好`→`浣犲ソ`）
     → `CbFixWide()` 用 GBK→UTF-8 回滚，失败则保留原文
  4. 基线必须在世界加载前建立，否则登录行会落在基线之前被跳过

### 17.4 投递

- 事件入 `std::deque`（上限 2000，超限计 `dropped`）
- 工作线程用 **WinHTTP** POST，`Connection: close`（避免单线程接收端被长连接卡死），失败重试一次
- 统计：`python scumctl.py cbstate` → `queued/sent/fail/dropped/logEvents/chatHooked`

### 17.5 本地接收端（验证用）

```
python .re\\cb_recv.py        # 多线程 HTTP，监听 127.0.0.1:8080，落盘 .re\\cb_events.log
```
- 必须以 `chcp 65001` + `PYTHONIOENCODING=utf-8` 启动窗口，否则中文显示乱码（文件本身是 UTF-8 正确的）

### 17.6 控制命令

```
python scumctl.py cbstate            # 状态与计数
python scumctl.py cbreload           # 重读 YG_CONFIG.json
python scumctl.py cbtest "hello"     # 投递合成事件
python scumctl.py cbloginfo login    # 查看某类日志文件的大小/偏移/落后字节
```

### 17.7 实测结果

| 事件 | 状态 |
|---|---|
| 聊天 `im`（含中文、频道、SteamID、名字） | ✅ `msg='你好' channel=2/3` |
| 登录 `login`（含 IP、坐标） | ✅ `action=login ip=192.168.1.112 position=X=...` |
| 登出 `login/logout` | ✅ |
| 其它日志（loot/gameplay/admin…） | ✅ 通用 text 事件 |
"""
with open(README, "a", encoding="utf-8") as f:
    f.write(section)
print("ok")
