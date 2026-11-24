#!/usr/bin/env python3
"""SCUM dedicated-server 状态巡检。

读取 D:\\SCUM_Server 下的 Steam 安装清单、服务器配置与启动脚本，
一次性报告：安装是否完成、端口配置是否一致、磁盘余量、可执行文件、日志尾部。

用法:
    python scripts/scum_status.py
    python scripts/scum_status.py --root D:\\SCUM_Server --log-tail 40
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

APP_ID = "3792580"
DEFAULT_ROOT = Path(r"D:\SCUM_Server")
SERVER_EXE = Path("SCUM/Binaries/Win64/SCUMServer-Win64-Shipping.exe")
LOGS_DIR = Path("SCUM/Saved/Logs")

# appmanifest StateFlags 位含义（Steam 客户端内部状态位）
STATE_FLAGS = {
    0x0001: "已安装 / 未更新",
    0x0002: "更新中",
    0x0004: "已完全安装",
    0x0020: "需要更新",
    0x0040: "已挂起",
    0x0400: "更新已暂停",
    0x1000: "更新已排队",
}


def parse_keyvalues(text: str) -> dict:
    """解析 Steam 的 Vala KeyValues 文本（ACF/VDF）。

    语法：字符串键后跟 字符串值 或 `{ ... }` 块。这里返回嵌套 dict。
    """
    pos = 0
    length = len(text)
    ws = " \t\r\n"

    def skip_ws() -> None:
        nonlocal pos
        while pos < length and text[pos] in ws:
            pos += 1

    def read_string() -> str:
        nonlocal pos
        skip_ws()
        if pos >= length or text[pos] != '"':
            raise ValueError(f"期望引号，实际在偏移 {pos} 遇到 {text[pos:pos + 1]!r}")
        pos += 1
        buf: list[str] = []
        while pos < length:
            ch = text[pos]
            if ch == "\\" and pos + 1 < length:
                buf.append(text[pos + 1])
                pos += 2
                continue
            if ch == '"':
                pos += 1
                return "".join(buf)
            buf.append(ch)
            pos += 1
        raise ValueError("字符串未闭合")

    def parse_block() -> dict:
        nonlocal pos
        block: dict = {}
        while True:
            skip_ws()
            if pos >= length:
                return block
            if text[pos] == "}":
                pos += 1
                return block
            if text[pos] == "{":  # 容错：孤立的左花括号
                pos += 1
                continue
            key = read_string()
            skip_ws()
            if pos < length and text[pos] == "{":
                pos += 1
                block[key] = parse_block()
            else:
                block[key] = read_string()

    return parse_block()


def parse_acf(path: Path) -> dict:
    """解析 appmanifest_*.acf，返回 AppState 这一层（或最外层）的键值。"""
    tree = parse_keyvalues(path.read_text(encoding="utf-8", errors="replace"))
    if len(tree) == 1:
        only = next(iter(tree.values()))
        if isinstance(only, dict):
            return only
    return tree


def decode_state_flags(raw: str) -> list[str]:
    try:
        flags = int(raw)
    except (TypeError, ValueError):
        return []
    return [name for bit, name in STATE_FLAGS.items() if flags & bit]


def parse_server_settings(path: Path) -> dict[str, str]:
    """读取 ServerSettings.ini，只取 scum.* 键。"""
    settings: dict[str, str] = {}
    if not path.is_file():
        return settings
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith(("[", ";", "#")) or "=" not in line:
            continue
        key, _, value = line.partition("=")
        settings[key.strip()] = value.strip()
    return settings


def parse_launch_args(bat: Path) -> dict[str, str]:
    """从 start_server.bat 里抓 -Key=Value 形式的启动参数。"""
    if not bat.is_file():
        return {}
    raw = bat.read_bytes().decode("gbk", errors="replace")
    return {m.group(1).lower(): m.group(2) for m in re.finditer(r"-(port|QueryPort|MaxPlayers)=(\S+)", raw)}


def report(root: Path, log_tail: int) -> int:
    server_dir = root / "server"
    acf = server_dir / "steamapps" / f"appmanifest_{APP_ID}.acf"
    ini = root / "config" / "ServerSettings.ini"

    print(f"== SCUM Server 状态巡检: {root}")
    problems: list[str] = []

    # --- 1. 安装状态 ---
    if not acf.is_file():
        print(f"[安装] 未找到清单 {acf}")
        problems.append("缺少 appmanifest，服务端从未开始安装")
    else:
        manifest = parse_acf(acf)
        installed = manifest.get("SizeOnDisk", "0")
        to_download = int(manifest.get("BytesToDownload", "0") or 0)
        to_stage = int(manifest.get("BytesToStage", "0") or 0)
        downloaded = int(manifest.get("BytesDownloaded", "0") or 0)
        state_raw = manifest.get("StateFlags", "0")
        states = decode_state_flags(state_raw)
        print(f"[安装] StateFlags={state_raw} ({', '.join(states) or '未知'})")
        print(f"[安装] SizeOnDisk={installed} bytes  buildid={manifest.get('buildid')} -> target={manifest.get('TargetBuildID')}")
        print(f"[安装] 下载 {downloaded}/{to_download} bytes  待落地 {to_stage} bytes")
        if to_download or to_stage:
            problems.append(
                f"安装未完成：仍需下载 {to_download / 2**30:.2f} GiB，落地 {to_stage / 2**30:.2f} GiB"
                "（重跑 install_update.bat）"
            )

    exe = server_dir / SERVER_EXE
    print(f"[可执行] {'存在' if exe.is_file() else '缺失'} -> {exe}")
    if not exe.is_file():
        problems.append("SCUMServer-Win64-Shipping.exe 不存在，start_server.bat 会直接退出")

    # --- 2. 配置 ---
    settings = parse_server_settings(ini)
    for key in ("scum.ServerName", "scum.ServerPort", "scum.ServerQueryPort", "scum.ServerMaxPlayers", "scum.ServerIsPublic"):
        print(f"[配置] {key} = {settings.get(key, '<缺失>')}")
    if not settings:
        problems.append("ServerSettings.ini 缺失或为空")

    # --- 3. 端口一致性 ---
    launch = parse_launch_args(root / "start_server.bat")
    ini_port = settings.get("scum.ServerPort")
    ini_query = settings.get("scum.ServerQueryPort")
    print(f"[启动参数] {launch or '<未解析到>'}")
    if ini_port and launch.get("port") and ini_port != launch["port"]:
        problems.append(f"端口不一致：ini={ini_port} vs bat=-port={launch['port']}")
    if ini_query and launch.get("queryport") and ini_query != launch["queryport"]:
        problems.append(f"查询端口不一致：ini={ini_query} vs bat=-QueryPort={launch['queryport']}")

    # --- 4. 磁盘 ---
    try:
        usage = shutil.disk_usage(root.anchor or root)
        free_gib = usage.free / 2**30
        print(f"[磁盘] {root.anchor} 可用 {free_gib:.1f} GiB")
        if free_gib < 20:
            problems.append(f"磁盘余量偏低（{free_gib:.1f} GiB），提交暂存数据需要约 15.7 GiB")
    except OSError as exc:
        print(f"[磁盘] 无法读取用量: {exc}")

    # --- 5. 暂存占用 ---
    staging = server_dir / "steamapps" / "downloading" / APP_ID
    if staging.is_dir():
        size = sum(p.stat().st_size for p in staging.rglob("*") if p.is_file())
        print(f"[暂存] {staging} 已占 {size / 2**30:.2f} GiB（未提交）")

    # --- 6. 日志 ---
    logs = server_dir / LOGS_DIR
    if logs.is_dir():
        newest = sorted(logs.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:1]
        if newest:
            print(f"[日志] {newest[0]}")
            tail = newest[0].read_text(encoding="utf-8", errors="replace").splitlines()[-log_tail:]
            for line in tail:
                print(f"  {line}")

    # --- 7. 结论 ---
    if problems:
        print("\n== 待处理")
        for idx, item in enumerate(problems, 1):
            print(f"  {idx}. {item}")
        return 1
    print("\n== 一切正常：服务端已安装，端口一致，可以 start_server.bat")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SCUM 专用服务器状态巡检")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="服务安装根目录")
    parser.add_argument("--log-tail", type=int, default=20, help="日志尾部行数")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出配置摘要")
    args = parser.parse_args(argv)

    if args.json:
        settings = parse_server_settings(args.root / "config" / "ServerSettings.ini")
        print(json.dumps(settings, ensure_ascii=False, indent=2))
        return 0
    return report(args.root, args.log_tail)


if __name__ == "__main__":
    sys.exit(main())
