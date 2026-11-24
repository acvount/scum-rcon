#!/usr/bin/env python3
"""scum_cb_recv.py -- 本地事件接收端（验证事件回调用）

插件把聊天/登录/日志事件以 JSON 逐条 POST 到 YG_CONFIG.json 里配置的 url。
本脚本在服务器本机起一个多线程 HTTP 服务，把收到的每条事件原样打印并追加到日志文件。

用法:
  python scum-harness\\client\\scum_cb_recv.py
  python scum-harness\\client\\scum_cb_recv.py --port 8080 --out events.jsonl

配合的插件配置（服务端 Binaries\\Win64\\YG_CONFIG.json）:
  {"enable": true, "url": "http://127.0.0.1:8080/scum/event"}
"""
import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = "events.jsonl"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        body = raw.decode("utf-8", "replace")
        print("[RECV]", body, flush=True)
        try:
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(body + "\n")
        except Exception as e:  # 落盘失败不影响应答
            print("write fail:", e, file=sys.stderr, flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--out", default="events.jsonl")
    ns = ap.parse_args()
    OUT = ns.out
    srv = ThreadingHTTPServer((ns.host, ns.port), Handler)
    srv.daemon_threads = True
    print(f"==== LISTENING {ns.host}:{ns.port} -> {ns.out} ====", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
